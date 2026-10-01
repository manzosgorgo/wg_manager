#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
import ast
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
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

BOUNDARY_NAMES = {
    "do_GET",
    "do_POST",
    "do_PUT",
    "do_DELETE",
    "do_PATCH",
    "do_HEAD",
    "do_OPTIONS",

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

PROTOCOL_MESSAGE_ROOTS = {
    "request",
    "auth",
    "validated_request",
    "activation",
    "response",
    "result",
    "message",
}
DEFAULT_EXCLUDES = {
    # Version control / IDE
    ".git",
    ".idea",

    # Python environments / caches
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",

    # JavaScript / build artifacts
    "node_modules",
    "dist",
    "build",
    "coverage",
    "tools",

    # Sensitive project data
    "login",
    "cert",
}

# Files which must never be copied into docs/ai/files/.
#
# These are matched against the complete filename, not only the extension.
#
# The goal here is deliberately conservative: the AI index should contain
# source and structural information, not credentials or private key material.
SENSITIVE_FILENAMES = {
    ".env",
}

SENSITIVE_EXTENSIONS = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".csr",
    ".srl",
}

SENSITIVE_NAME_PARTS = {
    "secret",
    "password",
    "passwd",
    "credential",
    "credentials",
}

# Public certificates are not particularly useful in the source snapshot and
# may contain infrastructure-identifying information. Keep them out as well.
SENSITIVE_EXTENSIONS.add(".crt")


TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".mjs",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".java",
    ".rs",
    ".go",
    ".sh",
    ".bash",
    ".zsh",
    ".ini",
    ".cfg",
    ".conf",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".md",
    ".txt",
    ".html",
    ".css",
    ".sql",
}
SOCKET_MODULES = {
    "socket",
}

TLS_NAMES = {
    "ssl.wrap_socket",
    "SSLContext.wrap_socket",
}

HTTP_SERVER_NAMES = {
    "http.server.HTTPServer",
    "http.server.ThreadingHTTPServer",
    "HTTPServer",
    "ThreadingHTTPServer",
}

HTTP_CLIENT_NAMES = {
    "http.client.HTTPConnection",
    "http.client.HTTPSConnection",
    "HTTPConnection",
    "HTTPSConnection",
}

SOCKET_METHODS = {
    "connect",
    "bind",
    "listen",
    "accept",
    "send",
    "sendall",
    "recv",
    "recv_into",
    "close",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_protocol_message_access(
    node: ast.AST,
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in PROTOCOL_MESSAGE_ROOTS

    if isinstance(node, ast.Attribute):
        return is_protocol_message_access(node.value)

    return False


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

def socket_transport(node: ast.Call) -> tuple[str | None, str | None]:
    family = None
    transport = None

    if node.args:
        family_expr = connection_expression(node.args[0])

        if family_expr == "socket.AF_UNIX":
            family = "UNIX"
        elif family_expr == "socket.AF_INET":
            family = "INET"
        elif family_expr == "socket.AF_INET6":
            family = "INET6"

    if len(node.args) >= 2:
        type_expr = connection_expression(node.args[1])

        if type_expr == "socket.SOCK_STREAM":
            transport = "TCP" if family in {"INET", "INET6"} else "UNIX"
        elif type_expr == "socket.SOCK_DGRAM":
            transport = "UDP" if family in {"INET", "INET6"} else "UNIX-DGRAM"

    return family, transport

def is_test_path(path: Path) -> bool:
    return "tests" in path.parts

def connection_dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        base = connection_dotted_name(node.value)
        if base:
            return f"{base}.{node.attr}"
        return node.attr

    return None


def connection_expression(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<unknown>"

def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def is_sensitive_file(path: Path) -> bool:
    """
    Return True if a file must never be copied into the AI source index.

    This check is intentionally conservative.
    """

    name = path.name.lower()

    if name in SENSITIVE_FILENAMES:
        return True

    if path.suffix.lower() in SENSITIVE_EXTENSIONS:
        return True

    # Check filename components such as:
    #   database_password.txt
    #   user_secret.json
    #   credentials.yaml
    stem = path.stem.lower()

    for part in SENSITIVE_NAME_PARTS:
        if part in stem:
            return True

    return False


def is_text_file(path: Path) -> bool:
    if is_sensitive_file(path):
        return False

    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True

    # Extensionless small files: try UTF-8.
    if path.suffix == "":
        try:
            path.read_text(encoding="utf-8")
            return True
        except (UnicodeDecodeError, OSError):
            return False

    return False


def git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def git_metadata(repo: Path) -> dict[str, str]:
    return {
        "commit": git(repo, "rev-parse", "HEAD"),
        "branch": git(repo, "branch", "--show-current"),
        "status": git(repo, "status", "--porcelain"),
    }


def relative(repo: Path, path: Path) -> str:
    return path.relative_to(repo).as_posix()


def is_relative_to(path: Path, parent: Path) -> bool:
    """
    Python 3.8-compatible equivalent of Path.is_relative_to().
    """

    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def collect_files(
    repo: Path,
    output: Path | None = None,
) -> list[Path]:
    """
    Collect files which belong to the project inventory.

    Generated output is always excluded, even when it is not explicitly
    present in DEFAULT_EXCLUDES.
    """

    files = []

    for path in repo.rglob("*"):
        if not path.is_file():
            continue

        # Never index the generated AI documentation itself.
        if output is not None and is_relative_to(path, output):
            continue

        rel_parts = path.relative_to(repo).parts

        if any(part in DEFAULT_EXCLUDES for part in rel_parts):
            continue

        files.append(path)

    return sorted(files)


def line_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except (UnicodeDecodeError, OSError):
        return 0


def source_target(
    path: Path,
    repo: Path,
    output: Path,
) -> Path:
    """
    Map:

        src/foo/bar.py

    to:

        docs/ai/files/src/foo/bar.py.md
    """

    rel = path.relative_to(repo)
    return output / "files" / Path(*rel.parts[:-1]) / f"{rel.name}.md"


def language_for(path: Path) -> str:
    suffix = path.suffix.lower()

    return {
        ".py": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cc": "cpp",
        ".java": "java",
        ".rs": "rust",
        ".go": "go",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
    }.get(suffix, "")

# ============================================================================
# Connection analysis
# ============================================================================

@dataclass
class ProtocolSurface:
    category: str
    file: Path
    symbol: str

    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    opaque: list[str] = field(default_factory=list)
    secure_session: list[str] = field(default_factory=list)

@dataclass
class ConnectionObservation:
    file: Path
    line: int
    kind: str
    symbol: str
    expression: str

@dataclass
class ConnectionResource:
    id: str
    root: str
    kind: str

    role: str | None = None
    transport: str | None = None
    family: str | None = None

    # For HTTP servers, this identifies the request-handler class.
    handler: str | None = None
    handler_file: str | None = None

    layers: list[str] = field(default_factory=list)
    variables: set[str] = field(default_factory=set)
    symbols: set[str] = field(default_factory=set)
    files: set[str] = field(default_factory=set)

    observations: list[ConnectionObservation] = field(
        default_factory=list
    )

    protocol_surfaces: list[ProtocolSurface] = field(
        default_factory=list
    )

    def add_layer(self, layer: str):
        if layer not in self.layers:
            self.layers.append(layer)

    def add_variable(self, variable: str):
        self.variables.add(variable)

    def add_symbol(self, symbol: str):
        if symbol:
            self.symbols.add(symbol)

    def add_observation(
        self,
        observation: ConnectionObservation,
    ):
        self.observations.append(observation)
        self.files.add(str(observation.file))

        if observation.symbol:
            self.symbols.add(observation.symbol)

    def add_protocol_surface(
        self,
        surface: ProtocolSurface,
    ):
        key = (
            surface.category,
            str(surface.file),
            surface.symbol,
        )

        for existing in self.protocol_surfaces:
            existing_key = (
                existing.category,
                str(existing.file),
                existing.symbol,
            )

            if existing_key == key:
                return

        self.protocol_surfaces.append(surface)

@dataclass
class ConnectionBinding:
    variable: str
    resource_id: str

class ConnectionAnalyzer(ast.NodeVisitor):

    def __init__(
        self,
        path: Path,
        repo: Path,
    ):
        self.path = path
        self.repo = repo

        self.class_stack: list[str] = []
        self.function_stack: list[str] = []

        self.observations: list[ConnectionObservation] = []

        # variable -> resource id
        self.bindings: dict[str, str] = {}
        # imported local symbol -> fully qualified name
        self.imports: dict[str, str] = {}
        # imported symbol -> source module
        self.imports: dict[str, str] = {}
        # resource id -> resource
        self.resources: dict[str, ConnectionResource] = {}

        self._resource_counter = 0

    # ------------------------------------------------------------
    # Context
    # ------------------------------------------------------------

    @property
    def current_symbol(self) -> str:
        if self.class_stack and self.function_stack:
            return (
                f"{'.'.join(self.class_stack)}."
                f"{'.'.join(self.function_stack)}"
            )

        if self.function_stack:
            return ".".join(self.function_stack)

        if self.class_stack:
            return ".".join(self.class_stack)

        return "<module>"

    # ------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------

    def new_resource(
        self,
        root: str,
        kind: str,
    ) -> ConnectionResource:

        self._resource_counter += 1

        resource_id = (
            f"connection-{self._resource_counter:03d}"
        )

        resource = ConnectionResource(
            id=resource_id,
            root=root,
            kind=kind,
        )

        self.resources[resource_id] = resource
        return resource

    def bind(
        self,
        variable: str,
        resource: ConnectionResource,
    ):
        self.bindings[variable] = resource.id
        resource.add_variable(variable)

    def resolve_name(
        self,
        name: str,
    ) -> ConnectionResource | None:

        resource_id = self.bindings.get(name)

        if resource_id is None:
            return None

        return self.resources.get(resource_id)

    def resolve_resource(
        self,
        node: ast.AST,
    ) -> ConnectionResource | None:

        # x
        if isinstance(node, ast.Name):
            return self.resolve_name(node.id)

        # x.socket
        if isinstance(node, ast.Attribute):
            return self.resolve_resource(node.value)

        return None
    def resolve_imported_symbol(
            self,
            name: str,
        ) -> str | None:
        return self.imports.get(name)
    def resolve_imported_file(
        self,
        name: str,
    ) -> Path | None:
        imported = self.imports.get(name)

        if not imported:
            return None

        module = imported.rsplit(".", 1)[0]

        relative_module = Path(
            *module.split(".")
        )

        candidate = (
            self.repo
            / relative_module
        ).with_suffix(".py")

        if candidate.is_file():
            return candidate

        package_init = (
            self.repo
            / relative_module
            / "__init__.py"
        )

        if package_init.is_file():
            return package_init

        return None
    # ------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------

    def observe(
        self,
        kind: str,
        node: ast.AST,
        resource: ConnectionResource | None = None,
    ):
        observation = ConnectionObservation(
            file=self.path,
            line=getattr(node, "lineno", 0),
            kind=kind,
            symbol=self.current_symbol,
            expression=connection_expression(node),
        )

        self.observations.append(observation)

        if resource is not None:
            resource.add_observation(observation)

    # ------------------------------------------------------------
    # Context visitors
    # ------------------------------------------------------------

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_stack.append(node.name)

        self.generic_visit(node)

        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.function_stack.append(node.name)

        self.generic_visit(node)

        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.function_stack.append(node.name)

        self.generic_visit(node)

        self.function_stack.pop()

    # ------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            for alias in node.names:
                if alias.name == "*":
                    continue

                local_name = alias.asname or alias.name

                self.imports[local_name] = (
                        f"{node.module}.{alias.name}"
                    )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            local_name = alias.asname or alias.name
            self.imports[local_name] = alias.name

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        resource = self.detect_resource_creation(node.value)

        if resource is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.bind(target.id, resource)

        else:
            source = self.resolve_resource(node.value)

            if source is not None:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.bind(target.id, source)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        resource = self.detect_resource_creation(node.value)

        if resource is not None:
            if isinstance(node.target, ast.Name):
                self.bind(node.target.id, resource)

        elif node.value is not None:
            source = self.resolve_resource(node.value)

            if source is not None:
                if isinstance(node.target, ast.Name):
                    self.bind(node.target.id, source)

        self.generic_visit(node)

    # ------------------------------------------------------------
    # Resource creation
    # ------------------------------------------------------------

    def detect_resource_creation(
        self,
        node: ast.AST | None,
    ) -> ConnectionResource | None:

        if not isinstance(node, ast.Call):
            return None

        name = connection_dotted_name(node.func)

        if name == "socket.socket":
            resource = self.new_resource(
                root=connection_expression(node),
                kind="socket",
            )
            family, transport = socket_transport(node)

            resource.family = family
            resource.transport = transport
            resource.add_layer("socket")

            self.observe(
                "SOCKET_CREATE",
                node,
                resource,
            )

            return resource

        if name == "socket.create_connection":
            resource = self.new_resource(
                root=connection_expression(node),
                kind="tcp-connection",
            )
            family, transport = socket_transport(node)

            resource.family = family
            resource.transport = transport
            resource.add_layer("TCP")

            self.observe(
                "TCP_CONNECT",
                node,
                resource,
            )

            return resource

        if name in HTTP_SERVER_NAMES:
            resource = self.new_resource(
                root=connection_expression(node),
                kind="http-server",
            )

            family, transport = socket_transport(node)

            resource.family = family
            resource.transport = transport
            resource.role = "server"

            resource.add_layer("TCP")
            resource.add_layer("HTTP")
            # HTTPServer(address, HandlerClass)
            #
            # The second positional argument identifies the request handler
            # class responsible for the HTTP protocol surface.
            if len(node.args) >= 2:
                handler = connection_dotted_name(node.args[1])

                if handler:
                    resource.handler = handler

                    handler_file = self.resolve_imported_file(handler)

                    if handler_file is not None:
                        resource.files.add(
                            relative(
                                self.repo,
                                handler_file,
                            )
                        )
            self.observe(
                "HTTP_SERVER",
                node,
                resource,
            )

            return resource

        if name in HTTP_CLIENT_NAMES:
            resource = self.new_resource(
                root=connection_expression(node),
                kind="http-client",
            )
            family, transport = socket_transport(node)

            resource.family = family
            resource.transport = transport
            resource.role = "client"

            if name.endswith("HTTPSConnection"):
                resource.add_layer("TCP")
                resource.add_layer("TLS")
                resource.add_layer("HTTP")
            else:
                resource.transport = "TCP"
                resource.add_layer("TCP")
                resource.add_layer("HTTP")

            self.observe(
                "HTTP_CLIENT",
                node,
                resource,
            )

            return resource

        return None

    # ------------------------------------------------------------
    # Calls
    # ------------------------------------------------------------

    def visit_Call(self, node: ast.Call):
        name = connection_dotted_name(node.func)

        # TLS wrapping of an existing resource.
        if name in {
            "ssl.wrap_socket",
            "SSLContext.wrap_socket",
        }:
            resource = None

            if node.args:
                resource = self.resolve_resource(node.args[0])

            if resource is not None:
                resource.add_layer("TLS")

                self.observe(
                    "TLS_WRAP",
                    node,
                    resource,
                )
            else:
                self.observe(
                    "TLS_WRAP",
                    node,
                )

            self.generic_visit(node)
            return

        # Methods operating on an existing resource.
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            resource = self.resolve_resource(node.func.value)

            if method in SOCKET_METHODS:
                if resource is not None:

                    if method == "connect":
                        resource.role = resource.role or "client"

                    self.observe(
                        method.upper(),
                        node,
                        resource,
                    )

                self.generic_visit(node)
                return

        self.generic_visit(node)


def extract_connection_resources(
    path: Path,
    repo: Path,
) -> list[ConnectionResource]:
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

    analyzer = ConnectionAnalyzer(
        path,
        repo,
    )
    analyzer.visit(tree)

    return list(analyzer.resources.values())

def attach_protocol_surfaces(
    connections: list[ConnectionResource],
    surfaces: list[ProtocolSurface],
    repo: Path,
):
    for connection in connections:
        for surface in surfaces:
            surface_file = relative(
                repo,
                surface.file,
            )

            if surface_file not in connection.files:
                continue

            # Direct correlation:
            #
            # connection symbol == protocol surface symbol
            #
            # Example:
            #   WGClientClient._request
            #
            #   -> WGClientClient._request
            if surface.symbol in connection.symbols:
                connection.add_protocol_surface(surface)
                continue

            # HTTP server correlation:
            #
            # HTTPServer(..., HandlerClass)
            #
            #   -> HandlerClass.do_GET()
            #   -> HandlerClass.do_POST()
            #   -> ...
            # HTTP handler correlation.
            if (
                connection.kind == "http-server"
                and connection.handler
                and surface.category == "HTTP"
            ):
                prefix = connection.handler + "."

                if surface.symbol.startswith(prefix):
                    connection.add_protocol_surface(surface)

def build_connections(
    repo: Path,
    files: list[Path],
    protocol_surfaces: list[ProtocolSurface],
) -> list[ConnectionResource]:
    connections: list[ConnectionResource] = []

    counter = 1

    for path in files:
        if path.suffix.lower() != ".py":
            continue

        resources = extract_connection_resources(
            path,
            repo,
        )
        for resource in resources:
            # Il counter globale serve soltanto a dare ID stabili
            # all'interno del documento finale.
            resource.id = f"connection-{counter:03d}"
            counter += 1

            # Le osservazioni contengono già il file assoluto.
            # Normalizziamo invece files a path relativi al repository.
            resource.files.add(relative(repo, path))
            connections.append(resource)

    attach_protocol_surfaces(
        connections,
        protocol_surfaces,
        repo,
    )
    return connections


def build_connections_document(
    repo: Path,
    files: list[Path],
    protocol_surfaces: list[ProtocolSurface],
) -> str:

    resources = build_connections(
        repo,
        files,
        protocol_surfaces,
    )
    production = []
    tests = []

    for resource in resources:
        if resource.files and all(
            is_test_path(Path(path))
            for path in resource.files
        ):
            tests.append(resource)
        else:
            production.append(resource)

    lines = [
        "# Connections",
        "",
        "Generated mechanically by `tools/project_index.py`.",
        "",
        "> **Observational only.**",
        "> This document describes communication resources and their",
        "> detected protocol layers.",
        "> It is not a normative architecture specification.",
        "",
        "## Summary",
        "",
        f"- Production connections: **{len(production)}**",
        f"- Test connections: **{len(tests)}**",
        "",
    ]

    def render_group(
        title: str,
        group: list[ConnectionResource],
    ):
        lines.append(f"## {title}")
        lines.append("")

        if not group:
            lines.append("_None detected._")
            lines.append("")
            return

        for resource in group:
            lines.append(f"### {resource.id}")
            lines.append("")

            lines.append(f"- **Kind:** {resource.kind}")

            if resource.role:
                lines.append(
                    f"- **Role:** {resource.role}"
                )
            if resource.handler:
                lines.append(f"- **Handler:** `{resource.handler}`")

            if resource.transport:
                lines.append(
                    f"- **Transport:** {resource.transport}"
                )

            lines.append("")

            if resource.layers:
                lines.append("**Layers:**")
                for layer in resource.layers:
                    lines.append(f"- {layer}")
                lines.append("")

            if resource.variables:
                lines.append("**Variables:**")
                for variable in sorted(resource.variables):
                    lines.append(f"- `{variable}`")
                lines.append("")

            if resource.files:
                lines.append("**Files:**")
                for path in sorted(resource.files):
                    lines.append(f"- `{path}`")
                lines.append("")

            if resource.symbols:
                lines.append("**Symbols:**")
                for symbol in sorted(resource.symbols):
                    lines.append(f"- `{symbol}`")
                lines.append("")

            if resource.observations:
                lines.append("**Evidence:**")

                for observation in sorted(
                    resource.observations,
                    key=lambda item: (
                        str(item.file),
                        item.line,
                    ),
                ):
                    relative_path = observation.file.relative_to(repo)

                    lines.append(
                        f"- `{relative_path}:{observation.line}` "
                        f"{observation.kind} "
                        f"`{observation.expression}`"
                    )
                if resource.protocol_surfaces:
                    lines.extend(
                        [
                            "",
                            "**Message surfaces:**",
                        ]
                    )

                    grouped: dict[str, list[ProtocolSurface]] = {}

                    for surface in resource.protocol_surfaces:
                        grouped.setdefault(
                            surface.category,
                            [],
                        ).append(surface)

                    for category, surfaces in sorted(grouped.items()):
                        lines.append(f"- **{category}**")

                        for surface in sorted(
                            surfaces,
                            key=lambda s: s.symbol,
                        ):
                            lines.append(f"  - `{surface.symbol}()`")

                            if surface.inputs:
                                lines.append(
                                    "    - **Inputs:** "
                                    + ", ".join(
                                        f"`{value}`" for value in surface.inputs
                                    )
                                )

                            if surface.outputs:
                                lines.append(
                                    "    - **Outputs:** "
                                    + ", ".join(
                                        f"`{value}`" for value in surface.outputs
                                    )
                                )

                            if surface.opaque:
                                lines.append(
                                    "    - **OPAQUE:** "
                                    + ", ".join(
                                        f"`{value}`" for value in surface.opaque
                                    )
                                )

                            if surface.secure_session:
                                lines.append(
                                    "    - **Secure session:** "
                                    + ", ".join(
                                        f"`{value}`" for value in surface.secure_session
                                    )
                                )

                lines.append("")
    render_group(
        "Production connections",
        production,
    )

    render_group(
        "Test connections",
        tests,
    )

    return "\n".join(lines)

# ----------------------------------------------------------------------------
# SYMBOLS
# ---------------------------------------------------------------------------

def format_python_annotation(node) -> str:
    """
    Return a compact source representation of a Python annotation.
    """
    import ast

    try:
        return ast.unparse(node)
    except (AttributeError, ValueError):
        return "..."


def format_python_arguments(node) -> str:
    """
    Reconstruct a readable Python function signature from an AST node.
    """
    import ast

    parts = []

    positional = list(node.args.posonlyargs) + list(node.args.args)
    defaults = [None] * (
        len(positional) - len(node.args.defaults)
    ) + list(node.args.defaults)

    for arg, default in zip(positional, defaults):
        text = arg.arg

        if arg.annotation:
            text += f": {format_python_annotation(arg.annotation)}"

        if default is not None:
            try:
                text += f" = {ast.unparse(default)}"
            except (AttributeError, ValueError):
                text += " = ..."

        parts.append(text)

    if node.args.vararg:
        text = f"*{node.args.vararg.arg}"

        if node.args.vararg.annotation:
            text += (
                f": {format_python_annotation(node.args.vararg.annotation)}"
            )

        parts.append(text)
    elif node.args.kwonlyargs:
        parts.append("*")

    for arg, default in zip(
        node.args.kwonlyargs,
        node.args.kw_defaults,
    ):
        text = arg.arg

        if arg.annotation:
            text += f": {format_python_annotation(arg.annotation)}"

        if default is not None:
            try:
                text += f" = {ast.unparse(default)}"
            except (AttributeError, ValueError):
                text += " = ..."

        parts.append(text)

    if node.args.kwarg:
        text = f"**{node.args.kwarg.arg}"

        if node.args.kwarg.annotation:
            text += (
                f": {format_python_annotation(node.args.kwarg.annotation)}"
            )

        parts.append(text)

    if node.returns:
        result = format_python_annotation(node.returns)
        return ", ".join(parts), result

    return ", ".join(parts), None


def extract_python_symbols(path: Path) -> list[dict]:
    """
    Extract structural symbols from a Python module.

    This function never imports or executes the target module.
    """

    import ast

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []

    symbols = []

    for node in tree.body:

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args, returns = format_python_arguments(node)

            prefix = "async " if isinstance(
                node,
                ast.AsyncFunctionDef,
            ) else ""

            signature = f"{prefix}def {node.name}({args})"

            if returns:
                signature += f" -> {returns}"

            symbols.append({
                "kind": "function",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "signature": signature,
            })

        elif isinstance(node, ast.ClassDef):
            bases = []

            for base in node.bases:
                try:
                    bases.append(ast.unparse(base))
                except (AttributeError, ValueError):
                    bases.append("...")

            symbols.append({
                "kind": "class",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "bases": bases,
            })

            for child in node.body:
                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):
                    args, returns = format_python_arguments(child)

                    prefix = "async " if isinstance(
                        child,
                        ast.AsyncFunctionDef,
                    ) else ""

                    signature = f"{prefix}def {child.name}({args})"

                    if returns:
                        signature += f" -> {returns}"

                    symbols.append({
                        "kind": "method",
                        "name": child.name,
                        "class": node.name,
                        "line": child.lineno,
                        "end_line": getattr(
                            child,
                            "end_lineno",
                            child.lineno,
                        ),
                        "signature": signature,
                    })

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.append({
                        "kind": "variable",
                        "name": target.id,
                        "line": node.lineno,
                        "end_line": getattr(
                            node,
                            "end_lineno",
                            node.lineno,
                        ),
                    })

        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                symbols.append({
                    "kind": "variable",
                    "name": node.target.id,
                    "line": node.lineno,
                    "end_line": getattr(
                        node,
                        "end_lineno",
                        node.lineno,
                    ),
                })

    return symbols
def extract_js_symbols(path: Path) -> list[dict]:
    """
    Lightweight structural extraction for JavaScript.

    This deliberately does not try to parse JavaScript completely.
    """

    import re

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    symbols = []

    patterns = [
        (
            "function",
            re.compile(
                r"^\s*(?:export\s+)?"
                r"(?:async\s+)?function\s+"
                r"([A-Za-z_$][\w$]*)\s*\(([^)]*)\)",
                re.MULTILINE,
            ),
        ),
        (
            "class",
            re.compile(
                r"^\s*(?:export\s+)?class\s+"
                r"([A-Za-z_$][\w$]*)"
                r"(?:\s+extends\s+([A-Za-z_$][\w$\.]*))?",
                re.MULTILINE,
            ),
        ),
        (
            "arrow",
            re.compile(
                r"^\s*(?:export\s+)?"
                r"(?:const|let|var)\s+"
                r"([A-Za-z_$][\w$]*)\s*="
                r"\s*(?:async\s*)?"
                r"(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
                re.MULTILINE,
            ),
        ),
    ]

    for kind, pattern in patterns:
        for match in pattern.finditer(source):
            line = source.count("\n", 0, match.start()) + 1

            entry = {
                "kind": kind,
                "name": match.group(1),
                "line": line,
            }

            if kind == "class" and match.group(2):
                entry["bases"] = [match.group(2)]

            symbols.append(entry)

    return sorted(
        symbols,
        key=lambda symbol: (
            symbol["line"],
            symbol["name"],
        ),
    )


def build_symbols(files, repo: Path) -> str:
    """Build a structural symbol index for source files."""
    lines = [
        "# Symbols",
        "",
        "Structural symbol index extracted mechanically from source files.",
        "",
    ]

    for path in files:
        symbols = []

        if path.suffix == ".py":
            symbols = extract_python_symbols(path)
        elif path.suffix in {".js", ".mjs", ".cjs"}:
            symbols = extract_js_symbols(path)

        if not symbols:
            continue

        rel = path.relative_to(repo)

        lines.append(f"## `{rel}`")
        lines.append("")

        # Keep classes and their methods together.
        class_symbols = {
            symbol["name"]: symbol
            for symbol in symbols
            if symbol["kind"] == "class"
        }

        methods_by_class = {
            class_name: []
            for class_name in class_symbols
        }

        top_level = []

        for symbol in symbols:
            kind = symbol["kind"]

            if kind == "method":
                class_name = symbol.get("class")

                if class_name in methods_by_class:
                    methods_by_class[class_name].append(symbol)
                else:
                    # Defensive fallback for symbols whose parent class
                    # cannot be resolved.
                    top_level.append(symbol)
            else:
                top_level.append(symbol)

        # Preserve source order for top-level symbols.
        top_level.sort(key=lambda symbol: symbol["line"])

        for symbol in top_level:
            kind = symbol["kind"]
            name = symbol["name"]
            line = symbol["line"]

            if kind == "class":
                bases = symbol.get("bases", [])

                if bases:
                    base_text = ", ".join(bases)
                    lines.append(
                        f"- **class** `{name}` ({base_text}) — line {line}"
                    )
                else:
                    lines.append(
                        f"- **class** `{name}` — line {line}"
                    )

                methods = methods_by_class.get(name, [])
                methods.sort(key=lambda symbol: symbol["line"])

                for method in methods:
                    signature = method.get("signature")
                    method_line = method["line"]

                    if signature:
                        lines.append(
                            f"  - **method** `{signature}` — line {method_line}"
                        )
                    else:
                        lines.append(
                            f"  - **method** `{method['name']}` — line {method_line}"
                        )

            elif kind in {"function", "async_function"}:
                signature = symbol.get("signature")

                if signature:
                    lines.append(
                        f"- **function** `{signature}` — line {line}"
                    )
                else:
                    lines.append(
                        f"- **function** `{name}` — line {line}"
                    )

            elif kind in {"variable", "constant"}:
                lines.append(
                    f"- **variable** `{name}` — line {line}"
                )

            else:
                lines.append(
                    f"- **{kind}** `{name}` — line {line}"
                )

        lines.append("")

    return "\n".join(lines)
# ---------------------------------------------------------------------------
# TREE
# ---------------------------------------------------------------------------

def build_tree(files: list[Path], repo: Path) -> str:
    root = {}

    for path in files:
        parts = path.relative_to(repo).parts
        node = root

        for part in parts:
            node = node.setdefault(part, {})

    lines = ["# Project Tree", ""]

    def render(node: dict, prefix: str = ""):
        entries = sorted(
            node.items(),
            key=lambda x: (not bool(x[1]), x[0]),
        )

        for index, (name, children) in enumerate(entries):
            last = index == len(entries) - 1
            branch = "└── " if last else "├── "

            lines.append(prefix + branch + name)

            if children:
                extension = "    " if last else "│   "
                render(children, prefix + extension)

    render(root)

    lines.append("")
    return "\n".join(lines)
@dataclass
class ProtocolExtractionState:
    category: str
    symbol: str

    inputs: set[str] = field(default_factory=set)
    outputs: set[tuple[str, ...]] = field(default_factory=set)
    opaque: set[str] = field(default_factory=set)
    secure_session: set[str] = field(default_factory=set)


class ProtocolExtractor(ast.NodeVisitor):
    def __init__(
        self,
        path: Path,
        repo: Path,
    ):
        self.path = path
        self.repo = repo
        self.surfaces: list[ProtocolSurface] = []

        self.class_stack: list[str] = []
        self.function_stack: list[ProtocolExtractionState] = []

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

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._function(node)

    def _function(self, node: ast.FunctionDef):
        class_name = (
            self.class_stack[-1]
            if self.class_stack
            else None
        )

        is_boundary = function_is_boundary(node.name, class_name)

        if not is_boundary:
            for child in node.body:
                self.visit(child)
            return
        if class_name:
            symbol = f"{class_name}.{node.name}"
        else:
            symbol = node.name

        category = self.detect_channel(
            class_name,
            node.name,
        )

        state = ProtocolExtractionState(
            category=category,
            symbol=symbol,
        )

        self.function_stack.append(state)

        for child in node.body:
            self.visit(child)

        self.function_stack.pop()

        self.surfaces.append(
            ProtocolSurface(
                category=state.category,
                file=self.path,
                symbol=state.symbol,
                inputs=sorted(state.inputs),
                outputs=[
                    "{" + ", ".join(fields) + "}" for fields in sorted(state.outputs)
                ],
                opaque=sorted(state.opaque),
                secure_session=sorted(state.secure_session),
            )
        )

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
                fields = dict_fields(node)

                if fields:
                    self.function_stack[-1].outputs.add(tuple(fields))

        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Field consumption
    # ------------------------------------------------------------------

    def visit_Subscript(self, node: ast.Subscript):
        if self.function_stack:
            base = dotted_name(node.value)

            field = None

            if isinstance(node.slice, ast.Constant):
                if isinstance(node.slice.value, str):
                    field = node.slice.value

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

        state = self.function_stack[-1]

        name = dotted_name(node.func)

        if not name:
            self.generic_visit(node)
            return

        basename = name.rsplit(".", 1)[-1]

        # JSON serialization
        if name == "json.dumps":
            if node.args:
                arg = node.args[0]

                if isinstance(arg, ast.Dict):
                    if protocol_dict(arg):
                        fields = dict_fields(arg)

                        if fields:
                            state.outputs.add(tuple(fields))
        # OPAQUE
        if (
            name in OPAQUE_NAMES
            or name.startswith("opaque.")
        ):
            state.opaque.add(name)

        # Secure session
        if (
            name in SECURE_NAMES
            or basename in SECURE_NAMES
            or "SecureSession" in name
        ):
            state.secure_session.add(name)

        self.generic_visit(node)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.generic_visit(node)
def extract_protocol_surfaces_from_python(
    path: Path,
    repo: Path,
) -> list[ProtocolSurface]:
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

    extractor = ProtocolExtractor(path,repo)
    extractor.visit(tree)

    return extractor.surfaces

def extract_protocol_surfaces(
    repo: Path,
    files: list[Path],
) -> list[ProtocolSurface]:

    surfaces: list[ProtocolSurface] = []

    for path in files:
        if path.suffix.lower() != ".py":
            continue

        surfaces.extend(
            extract_protocol_surfaces_from_python(path,repo)
        )

    return surfaces

# ---------------------------------------------------------------------------
# MODULES
# ---------------------------------------------------------------------------

def build_modules(files: list[Path], repo: Path) -> str:
    directories = defaultdict(list)

    for path in files:
        rel = path.relative_to(repo)
        parent = rel.parent.as_posix()

        if parent == ".":
            parent = "/"

        directories[parent].append(rel.name)

    lines = [
        "# Modules / Directories",
        "",
        "This file is generated automatically.",
        "",
        "| Directory | Files |",
        "|---|---:|",
    ]

    for directory in sorted(directories):
        lines.append(
            f"| `{directory}` | {len(directories[directory])} |"
        )

    lines += [
        "",
        "## Contents",
        "",
    ]

    for directory in sorted(directories):
        lines.append(f"### `{directory}`")
        lines.append("")

        for filename in sorted(directories[directory]):
            lines.append(f"- `{filename}`")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------------

def extract_python_imports(path: Path) -> list[str]:
    """
    Lightweight import extraction.

    We intentionally do not import/execute the module.
    """

    import ast

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []

    result = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                result.add(node.module)

    return sorted(result)


def extract_js_imports(path: Path) -> list[str]:
    """
    Deliberately lightweight JS import extraction.

    This is not a JavaScript parser. It only records obvious
    static import/require declarations.
    """

    import re

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    patterns = [
        r"""import\s+(?:.+?\s+from\s+)?["']([^"']+)["']""",
        r"""import\s*\(\s*["']([^"']+)["']\s*\)""",
        r"""require\s*\(\s*["']([^"']+)["']\s*\)""",
    ]

    result = set()

    for pattern in patterns:
        for match in re.finditer(pattern, source):
            result.add(match.group(1))

    return sorted(result)


def build_dependencies(files: list[Path], repo: Path) -> str:
    dependencies = {}

    for path in files:
        suffix = path.suffix.lower()

        if suffix == ".py":
            deps = extract_python_imports(path)
        elif suffix in {".js", ".mjs"}:
            deps = extract_js_imports(path)
        else:
            deps = []

        if deps:
            dependencies[relative(repo, path)] = deps

    lines = [
        "# Dependencies",
        "",
        "This file is generated automatically.",
        "",
    ]

    for filename in sorted(dependencies):
        lines.append(f"## `{filename}`")
        lines.append("")

        for dep in dependencies[filename]:
            lines.append(f"- `{dep}`")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# FILE INDEX
# ---------------------------------------------------------------------------

def write_file_index(
    path: Path,
    repo: Path,
    output: Path,
) -> Path | None:
    """
    Write a Markdown representation of one source file.

    Sensitive files are rejected here as a second safety layer, even if
    collect_files() accidentally lets one through.
    """

    if is_sensitive_file(path):
        return None

    rel = relative(repo, path)
    target = source_target(path, repo, output)

    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

    language = language_for(path)
    digest = sha256(path)
    lines = line_count(path)

    imports = []

    suffix = path.suffix.lower()

    if suffix == ".py":
        imports = extract_python_imports(path)
    elif suffix in {".js", ".mjs"}:
        imports = extract_js_imports(path)

    with target.open("w", encoding="utf-8") as f:
        f.write(f"# `{rel}`\n\n")

        f.write("## Metadata\n\n")
        f.write(f"- Path: `{rel}`\n")
        f.write(f"- Language: `{language or 'unknown'}`\n")
        f.write(f"- Lines: {lines}\n")
        f.write(f"- SHA256: `{digest}`\n")

        if imports:
            f.write("- Imports:\n")

            for dep in imports:
                f.write(f"  - `{dep}`\n")

        f.write("\n## Source\n\n")

        fence = language if language else ""

        f.write(f"```{fence}\n")
        f.write(source)

        if not source.endswith("\n"):
            f.write("\n")

        f.write("```\n")

    return target


# ---------------------------------------------------------------------------
# FILES README
# ---------------------------------------------------------------------------

def build_files_readme(
    files: list[Path],
    indexed: list[Path],
    repo: Path,
) -> str:
    indexed_set = {path for path in indexed}

    lines = [
        "# Indexed Source Files",
        "",
        "This directory contains generated Markdown representations of "
        "project source files.",
        "",
        "The directory structure mirrors the original project tree.",
        "",
        "Sensitive files and generated/build directories are deliberately "
        "excluded.",
        "",
        f"- Project files in inventory: {len(files)}",
        f"- Text files indexed: {len(indexed)}",
        f"- Files without source snapshot: {len(files) - len(indexed)}",
        "",
    ]

    skipped = [
        path
        for path in files
        if path not in indexed_set
    ]

    if skipped:
        lines += [
            "## Files without source snapshot",
            "",
        ]

        for path in skipped:
            lines.append(f"- `{relative(repo, path)}`")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# INDEX
# ---------------------------------------------------------------------------

def build_index(
    repo: Path,
    files: list[Path],
    indexed: list[Path],
    metadata: dict[str, str],
) -> str:
    lines = [
        "# wg_manager AI Index",
        "",
        "> Generated automatically by `tools/project_index.py`.",
        "",
        "## Repository",
        "",
        f"- Root: `{repo}`",
        f"- Commit: `{metadata['commit']}`",
        f"- Branch: `{metadata['branch']}`",
        f"- Files in inventory: {len(files)}",
        f"- Text files indexed: {len(indexed)}",
        "",
    ]

    if metadata["status"]:
        lines += [
            "### Working tree",
            "",
            "The working tree contains uncommitted changes.",
            "",
        ]
    else:
        lines += [
            "### Working tree",
            "",
            "Clean.",
            "",
        ]

    lines += [
        "## Generated documents",
        "",
        "- [TREE.md](TREE.md)",
        "- [MODULES.md](MODULES.md)",
        "- [DEPENDENCIES.md](DEPENDENCIES.md)",
        "- [SYMBOLS.md](SYMBOLS.md)",
        "- [CONNECTIONS.md](CONNECTIONS.md)",
        "",
        "## Protocol snapshots",
        "",
        "- [wg_auth_proto.md](wg_auth_proto.md)",
        "- [wg_client_proto.md](wg_client_proto.md)",
        "- [wg_manager_proto.md](wg_manager_proto.md)",
        "",
        "## Source files",
        "",
        "- [files/](files/)",
        "",
    ]
    for path in indexed:
        rel = relative(repo, path)

        target = source_target(path, repo, Path("."))

        # target is only used to construct the relative files/... path.
        # Convert it explicitly rather than depending on filesystem paths.
        target_rel = Path("files") / Path(*Path(rel).parts[:-1]) / (
            Path(rel).name + ".md"
        )

        lines.append(
            f"- `{rel}` → [{target_rel.as_posix()}]"
            f"({target_rel.as_posix()})"
        )

    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a static AI-readable index of the project."
    )

    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Project root (default: current directory)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="docs/ai",
        help="Output directory (default: docs/ai)",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove generated AI documentation before regenerating",
    )

    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    output = (repo / args.output).resolve()

    if not repo.is_dir():
        raise SystemExit(
            f"error: repository does not exist: {repo}"
        )

    # Safety check: output must live inside the repository.
    if not is_relative_to(output, repo):
        raise SystemExit(
            "error: output directory must be inside the repository"
        )

    if args.clean and output.exists():
        shutil.rmtree(output)

    output.mkdir(parents=True, exist_ok=True)

    files = collect_files(repo, output)
    metadata = git_metadata(repo)

    indexed = []

    for path in files:
        if is_text_file(path):
            target = write_file_index(path, repo, output)

            if target is not None:
                indexed.append(path)

    indexed.sort()

    (output / "TREE.md").write_text(
        build_tree(files, repo),
        encoding="utf-8",
    )

    (output / "MODULES.md").write_text(
        build_modules(files, repo),
        encoding="utf-8",
    )

    (output / "DEPENDENCIES.md").write_text(
        build_dependencies(files, repo),
        encoding="utf-8",
    )

    (output / "SYMBOLS.md").write_text(
        build_symbols(files, repo),
        encoding="utf-8",
    )
    protocol_surfaces = extract_protocol_surfaces(
        repo,
        files,
    )

    (output / "CONNECTIONS.md").write_text(
        build_connections_document(
            repo,
            files,
            protocol_surfaces,
        ),
        encoding="utf-8",
    )

    (output / "files" / "README.md").write_text(
        build_files_readme(files, indexed, repo),
        encoding="utf-8",
    )

    (output / "README.md").write_text(
        build_index(repo, files, indexed, metadata),
        encoding="utf-8",
    )

    print(f"Files in inventory: {len(files)}")
    print(f"Text files indexed: {len(indexed)}")
    print(f"Output: {output}")


if __name__ == "__main__":
    main()
