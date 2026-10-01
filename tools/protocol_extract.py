#!/usr/bin/env python3

"""
Protocol map extractor.

This tool extracts a compact, observational map of the protocols
implemented by the project.

It intentionally does NOT attempt to produce a normative specification.

The extractor focuses on protocol boundaries:

    HTTP endpoints
    IPC messages
    JSON request/response objects
    authentication messages
    activation messages
    secure-session authentication
    state transitions

Tests are used only as supporting evidence and are not emitted as
individual protocol sections.

Output:

    docs/ai/protocol-extracted.md
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


# ============================================================================
# Configuration
# ============================================================================

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "login",
}

EXCLUDED_TOP_LEVEL = {
    "tests",
    "tools",
}

SENSITIVE_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".csr",
    ".srl",
    ".crt",
}

SENSITIVE_NAMES = {
    ".env",
}

PROTOCOL_FIELDS = {
    "protocol_version",
    "type",
    "status",
    "ok",
    "error",
    "message",

    "username",
    "pub",
    "auth",
    "authenticated",

    "session_id",
    "k_session",
    "activation",
    "expires_at",
    "created_at",
    "timeout",

    "client_id",
    "listen_path",

    "interface",
    "peer",
    "peers",
    "public_key",
    "private_key",
    "allowed_ip",
    "allowed_ips",
    "endpoint",

    "counter",
    "nonce",
    "mac",
}

# These names are strong indicators that a function sits on a
# protocol boundary.
BOUNDARY_NAMES = {
    "do_GET",
    "do_POST",
    "do_PUT",
    "do_DELETE",

    "activate",
    "activate_client",
    "deactivate",

    "start_authentication",
    "finish_authentication",

    "create_credential_response",
    "authenticate",

    "send_result",
    "send_packet",

    "request_auth_headers",
    "authenticate_request",
    "_authenticated_headers",

    "add_peer",
    "remove_peer",
    "status",
    "peers",
}

OPAQUE_NAMES = {
    "opaque.Ids",
    "opaque.CreateCredentialResponse",
    "opaque.UserAuth",
    "opaque.CreateRegistrationRequest",
    "opaque.CreateRegistrationResponse",
    "opaque.FinalizeRequest",
    "opaque.StoreUserRecord",
}

SECURE_NAMES = {
    "WGSecureSession",
    "create_request_auth",
    "create_response_auth",
    "verify_request",
    "verify_response",
}


# ============================================================================
# Data structures
# ============================================================================

@dataclass(frozen=True)
class Message:
    fields: tuple[str, ...]


@dataclass
class Endpoint:
    channel: str
    name: str
    path: str | None = None

    inputs: set[str] = field(default_factory=set)
    outputs: set[Message] = field(default_factory=set)

    states: set[str] = field(default_factory=set)
    opaque: set[str] = field(default_factory=set)
    secure: set[str] = field(default_factory=set)

    evidence: set[str] = field(default_factory=set)

    def add_message(self, fields):
        fields = tuple(
            dict.fromkeys(
                field
                for field in fields
                if field
            )
        )

        if fields:
            self.outputs.add(
                Message(fields)
            )


# ============================================================================
# General helpers
# ============================================================================
# Objects whose attributes represent fields consumed from a
# protocol message.  This is intentionally strict: arbitrary
# attribute access is not considered protocol input.
PROTOCOL_MESSAGE_ROOTS = {
    "request",
    "auth",
    "validated_request",
    "activation",
    "response",
    "result",
    "message",
}


def is_protocol_message_access(
    node: ast.AST,
) -> bool:
    """
    Return True if an attribute/subscript access starts from an
    object that represents a protocol message.

    Examples accepted:

        request.username
        request["username"]
        auth.auth
        activation.session_id
        validated_request.counter

    Examples deliberately ignored:

        self.username
        self.config.auth
        self.controller.status
        self.server.interface
        exc.message
        log.error
    """

    if isinstance(node, ast.Name):
        return node.id in PROTOCOL_MESSAGE_ROOTS

    if isinstance(node, ast.Attribute):
        return is_protocol_message_access(node.value)

    return False

def is_sensitive(path: Path) -> bool:
    if path.name in SENSITIVE_NAMES:
        return True

    if path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True

    stem = path.stem.lower()

    return any(
        token in stem
        for token in (
            "secret",
            "password",
            "passwd",
            "credential",
            "credentials",
        )
    )


def collect_files(repo: Path) -> list[Path]:
    result = []

    for path in repo.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in EXCLUDED_DIRS
            for part in path.parts
        ):
            continue

        try:
            rel = path.relative_to(repo)
        except ValueError:
            continue

        if rel.parts and rel.parts[0] in EXCLUDED_TOP_LEVEL:
            continue

        if is_sensitive(path):
            continue

        if path.suffix.lower() not in {
            ".py",
            ".js",
            ".mjs",
            ".cjs",
        }:
            continue

        result.append(path)

    return sorted(result)


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)

        if base:
            return f"{base}.{node.attr}"

        return node.attr

    return None


def string_value(node: ast.AST) -> str | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    ):
        return node.value

    return None


def dict_fields(node: ast.Dict) -> list[str]:
    fields = []

    for key in node.keys:
        if key is None:
            continue

        value = string_value(key)

        if value is not None:
            fields.append(value)

    return fields


def protocol_dict(node: ast.Dict) -> bool:
    return bool(
        set(dict_fields(node))
        & PROTOCOL_FIELDS
    )


def function_is_boundary(
    name: str,
    class_name: str | None,
) -> bool:
    if name in BOUNDARY_NAMES:
        return True

    if class_name:
        if (
            "Handler" in class_name
            and name.startswith("do_")
        ):
            return True

    if (
        "auth" in name.lower()
        or "activation" in name.lower()
        or "session" in name.lower()
    ):
        return True

    return False


# ============================================================================
# Python extraction
# ============================================================================

class PythonExtractor(ast.NodeVisitor):

    def __init__(self):
        self.endpoints: list[Endpoint] = []

        self.class_stack: list[str] = []
        self.function_stack: list[Endpoint] = []

    # ------------------------------------------------------------------
    # Classes
    # ------------------------------------------------------------------

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_stack.append(node.name)

        for child in node.body:
            self.visit(child)

        self.class_stack.pop()

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------

    def visit_FunctionDef(self, node):
        self._function(node)

    def visit_AsyncFunctionDef(self, node):
        self._function(node)

    def _function(self, node):
        class_name = (
            self.class_stack[-1]
            if self.class_stack
            else None
        )

        if not function_is_boundary(
            node.name,
            class_name,
        ):
            # We still walk the function because a nested boundary
            # can theoretically exist.
            for child in node.body:
                self.visit(child)

            return

        if class_name:
            name = f"{class_name}.{node.name}"
        else:
            name = node.name

        channel = self.detect_channel(
            class_name,
            node.name,
        )

        endpoint = Endpoint(
            channel=channel,
            name=name,
        )

        self.endpoints.append(endpoint)
        self.function_stack.append(endpoint)

        for child in node.body:
            self.visit(child)

        self.function_stack.pop()

    # ------------------------------------------------------------------
    # Channel detection
    # ------------------------------------------------------------------

    @staticmethod
    def detect_channel(
        class_name: str | None,
        function_name: str,
    ) -> str:

        if class_name:
            if "IPC" in class_name:
                return "IPC"

            if "Handler" in class_name:
                return "HTTP"

        if "auth" in function_name.lower():
            return "AUTH"

        if "activation" in function_name.lower():
            return "ACTIVATION"

        return "INTERNAL"

    # ------------------------------------------------------------------
    # Dicts
    # ------------------------------------------------------------------

    def visit_Dict(self, node: ast.Dict):
        if self.function_stack:
            if protocol_dict(node):
                self.function_stack[-1].add_message(
                    dict_fields(node)
                )

        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Field consumption
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Field consumption
    # ------------------------------------------------------------------

    def visit_Subscript(self, node: ast.Subscript):
        if self.function_stack:
            base = dotted_name(node.value)

            field = None

            if isinstance(
                node.slice,
                ast.Constant,
            ):
                field = (
                    node.slice.value
                    if isinstance(
                        node.slice.value,
                        str,
                    )
                    else None
                )

            if (
                base
                and field in PROTOCOL_FIELDS
                and is_protocol_message_access(node.value)
            ):
                self.function_stack[-1].inputs.add(
                    f"{base}.{field}"
                )

        self.generic_visit(node)
    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------

    def visit_Attribute(self, node: ast.Attribute):
        if self.function_stack:
            if (
                node.attr in PROTOCOL_FIELDS
                and is_protocol_message_access(node.value)
            ):
                base = dotted_name(node.value)

                if base:
                    self.function_stack[-1].inputs.add(
                        f"{base}.{node.attr}"
                    )

        self.generic_visit(node)
    # ------------------------------------------------------------------
    # Calls
    # ------------------------------------------------------------------

    def visit_Call(self, node: ast.Call):
        if not self.function_stack:
            self.generic_visit(node)
            return

        endpoint = self.function_stack[-1]

        name = dotted_name(node.func)

        if not name:
            self.generic_visit(node)
            return

        basename = name.rsplit(".", 1)[-1]

        # --------------------------------------------------------------
        # JSON serialization
        # --------------------------------------------------------------

        if name == "json.dumps":
            if node.args:
                arg = node.args[0]

                if isinstance(arg, ast.Dict):
                    if protocol_dict(arg):
                        endpoint.add_message(
                            dict_fields(arg)
                        )

        # --------------------------------------------------------------
        # JSON deserialization
        # --------------------------------------------------------------

        # We don't emit this separately. The presence of consumed
        # protocol fields is enough to establish message consumption.

        # --------------------------------------------------------------
        # OPAQUE
        # --------------------------------------------------------------

        if (
            name in OPAQUE_NAMES
            or name.startswith("opaque.")
        ):
            endpoint.opaque.add(name)

        # --------------------------------------------------------------
        # Secure session
        # --------------------------------------------------------------

        if (
            name in SECURE_NAMES
            or basename in SECURE_NAMES
            or "SecureSession" in name
        ):
            endpoint.secure.add(name)

        # --------------------------------------------------------------
        # HTTP path
        # --------------------------------------------------------------

        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {
                "send_response",
            }
        ):
            endpoint.evidence.add(
                "HTTP response"
            )

        self.generic_visit(node)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def visit_Assign(self, node: ast.Assign):
        if self.function_stack:
            endpoint = self.function_stack[-1]

            state = self.extract_state(node.value)

            if state:
                endpoint.states.add(state)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if self.function_stack:
            endpoint = self.function_stack[-1]

            if node.value:
                state = self.extract_state(
                    node.value
                )

                if state:
                    endpoint.states.add(state)

        self.generic_visit(node)

    @staticmethod
    def extract_state(node):
        name = dotted_name(node)

        if not name:
            return None

        if "STATE_" in name:
            return name

        return None


def extract_python(path: Path) -> list[Endpoint]:
    try:
        source = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        tree = ast.parse(source)

    except (
        OSError,
        SyntaxError,
    ):
        return []

    extractor = PythonExtractor()
    extractor.visit(tree)

    return extractor.endpoints


# ============================================================================
# Merge / normalization
# ============================================================================

def endpoint_key(endpoint: Endpoint):
    return (
        endpoint.channel,
        endpoint.name,
    )


def merge_endpoints(
    endpoints: list[Endpoint],
) -> list[Endpoint]:

    merged: dict[tuple, Endpoint] = {}

    for endpoint in endpoints:
        key = endpoint_key(endpoint)

        if key not in merged:
            merged[key] = Endpoint(
                channel=endpoint.channel,
                name=endpoint.name,
                path=endpoint.path,
            )

        target = merged[key]

        target.inputs.update(
            endpoint.inputs
        )

        target.outputs.update(
            endpoint.outputs
        )

        target.states.update(
            endpoint.states
        )

        target.opaque.update(
            endpoint.opaque
        )

        target.secure.update(
            endpoint.secure
        )

        target.evidence.update(
            endpoint.evidence
        )

    return list(merged.values())


# ============================================================================
# Filtering
# ============================================================================

def is_noise(endpoint: Endpoint) -> bool:
    """
    Remove things that technically touch protocol-looking data but
    are not useful for reconstructing the protocol.
    """

    name = endpoint.name.lower()

    if name.endswith(".load_config"):
        return True

    if name.endswith(".__init__"):
        return True

    if name.endswith(".send_json"):
        return True

    if name.endswith("._send_json"):
        return True

    if name.endswith("._read_json"):
        return True

    if name.endswith(".parse_packet"):
        return True

    if name.endswith(".receive_packet"):
        return True

    if name.endswith(".send_packet"):
        return True

    if name.endswith("._validate_request_auth"):
        return True

    if name.endswith("._validate_response_auth"):
        return True

    if (
        not endpoint.inputs
        and not endpoint.outputs
        and not endpoint.states
        and not endpoint.opaque
        and not endpoint.secure
    ):
        return True

    return False


# ============================================================================
# Markdown
# ============================================================================

def render_message(message: Message) -> list[str]:
    lines = [
        "```text",
        "{",
    ]

    for field in message.fields:
        lines.append(
            f"  {field}"
        )

    lines.extend([
        "}",
        "```",
    ])

    return lines


def render_endpoint(
    endpoint: Endpoint,
) -> str:

    lines = []

    lines.append(
        f"### `{endpoint.name}()`"
    )

    # ---------------------------------------------------------------
    # IN
    # ---------------------------------------------------------------

    if endpoint.inputs:
        lines.append("")
        lines.append("**IN**")

        for item in sorted(endpoint.inputs):
            lines.append(
                f"- `{item}`"
            )

    # ---------------------------------------------------------------
    # OUT
    # ---------------------------------------------------------------

    if endpoint.outputs:
        lines.append("")
        lines.append("**OUT**")

        for message in sorted(
            endpoint.outputs,
            key=lambda x: x.fields,
        ):
            lines.extend(
                render_message(message)
            )

    # ---------------------------------------------------------------
    # STATE
    # ---------------------------------------------------------------

    if endpoint.states:
        lines.append("")
        lines.append("**STATE**")

        for state in sorted(endpoint.states):
            lines.append(
                f"- `{state}`"
            )

    # ---------------------------------------------------------------
    # AUTH
    # ---------------------------------------------------------------

    if endpoint.opaque:
        lines.append("")
        lines.append("**OPAQUE**")

        for item in sorted(endpoint.opaque):
            lines.append(
                f"- `{item}`"
            )

    if endpoint.secure:
        lines.append("")
        lines.append("**SECURE SESSION**")

        for item in sorted(endpoint.secure):
            lines.append(
                f"- `{item}`"
            )

    lines.append("")

    return "\n".join(lines)


def render_channel(
    channel: str,
    endpoints: list[Endpoint],
) -> str:

    lines = [
        f"## {channel}",
        "",
    ]

    for endpoint in sorted(
        endpoints,
        key=lambda e: e.name,
    ):
        lines.append(
            render_endpoint(endpoint)
        )

    return "\n".join(lines)


# ============================================================================
# High-level protocol summary
# ============================================================================

def build_protocol_overview(
    endpoints: list[Endpoint],
) -> str:

    lines = [
        "## Detected protocol surfaces",
        "",
    ]

    channels = {}

    for endpoint in endpoints:
        channels.setdefault(
            endpoint.channel,
            [],
        ).append(endpoint)

    preferred_order = [
        "AUTH",
        "ACTIVATION",
        "HTTP",
        "IPC",
        "INTERNAL",
    ]

    for channel in preferred_order:
        if channel not in channels:
            continue

        names = sorted(
            endpoint.name
            for endpoint in channels[channel]
        )

        lines.append(
            f"- **{channel}**: "
            + ", ".join(
                f"`{name}()`"
                for name in names
            )
        )

    lines.append("")

    return "\n".join(lines)


# ============================================================================
# Main document
# ============================================================================

def build_document(
    repo: Path,
    files: list[Path],
) -> str:

    all_endpoints = []

    for path in files:
        if path.suffix.lower() != ".py":
            continue

        all_endpoints.extend(
            extract_python(path)
        )

    all_endpoints = merge_endpoints(
        all_endpoints
    )

    all_endpoints = [
        endpoint
        for endpoint in all_endpoints
        if not is_noise(endpoint)
    ]

    channels = {}

    for endpoint in all_endpoints:
        channels.setdefault(
            endpoint.channel,
            [],
        ).append(endpoint)

    total = len(all_endpoints)

    lines = [
        "# Protocol Extracted",
        "",
        "Generated mechanically by "
        "`tools/protocol_extract.py`.",
        "",
        "> **Observational only.**",
        "> This document describes structures detected in source code.",
        "> It is not a normative protocol specification.",
        "",
        "## Summary",
        "",
        f"- Source files scanned: **{len(files)}**",
        f"- Protocol surfaces: **{total}**",
        "",
        "The extractor deliberately suppresses implementation details",
        "such as generic JSON helpers, configuration loading, socket",
        "plumbing and validation internals.",
        "",
        build_protocol_overview(
            all_endpoints
        ),
    ]

    for channel in (
        "AUTH",
        "ACTIVATION",
        "HTTP",
        "IPC",
        "INTERNAL",
    ):
        if channel not in channels:
            continue

        lines.append(
            render_channel(
                channel,
                channels[channel],
            )
        )

    return "\n".join(lines)


# ============================================================================
# Entry point
# ============================================================================

def main():
    repo = Path(__file__).resolve().parent.parent

    output_dir = (
        repo
        / "docs"
        / "ai"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = collect_files(repo)

    document = build_document(
        repo,
        files,
    )

    output = (
        output_dir
        / "protocol-extracted.md"
    )

    output.write_text(
        document,
        encoding="utf-8",
    )

    print(
        f"Wrote {output}"
    )


if __name__ == "__main__":
    main()