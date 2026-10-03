#!/usr/bin/env python3
"""Generate JSDoc HTML for the production frontend under docs/ai/jsdoc."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "src" / "wg_frontend"
OUTPUT = ROOT / "docs" / "ai" / "jsdoc"
CONFIG = ROOT / "tools" / "jsdoc.json"
PACKAGE_JSON = FRONTEND / "package.json"
LOCAL_JSDOC = FRONTEND / "node_modules" / ".bin" / "jsdoc"
JSDOC_VERSION = "4.0.5"

SOURCE_FILES = (
    FRONTEND / "wg_auth_session.js",
    FRONTEND / "wg_client_api.js",
    FRONTEND / "wg_client_errors.js",
    FRONTEND / "wg_opaque_client.js",
    FRONTEND / "wg_secure_session.js",
    FRONTEND / "www" / "vpn" / "app.js",
)


def jsdoc_command() -> list[str]:
    """Return a pinned JSDoc command, preferring the local dev dependency."""
    if LOCAL_JSDOC.is_file():
        return [str(LOCAL_JSDOC)]

    npx = shutil.which("npx")
    if npx is None:
        raise RuntimeError(
            "JSDoc is not installed and npx is unavailable; "
            "run 'cd src/wg_frontend && npm install'"
        )

    return [npx, "--yes", f"jsdoc@{JSDOC_VERSION}"]


def validate_sources() -> None:
    """Fail before generation if a configured production source is missing."""
    missing = [path for path in SOURCE_FILES if not path.is_file()]
    if missing:
        formatted = ", ".join(str(path.relative_to(ROOT)) for path in missing)
        raise RuntimeError(f"missing JavaScript documentation source(s): {formatted}")


def print_generated_tree(root: Path) -> None:
    """Print the generated file tree to stderr for failed output discovery."""
    print(f"[jsdoc] generated tree under {root}:", file=sys.stderr)

    entries = sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file()
    )

    if not entries:
        print("  <empty>", file=sys.stderr)
        return

    for path in entries[:200]:
        print(f"  {path}", file=sys.stderr)

    if len(entries) > 200:
        print(
            f"  ... {len(entries) - 200} more file(s)",
            file=sys.stderr,
        )


def find_site_root(build_output: Path) -> Path | None:
    """Find the directory containing JSDoc's generated index.html."""
    indexes = sorted(build_output.rglob("index.html"))

    if not indexes:
        return None

    if len(indexes) > 1:
        print(
            "[jsdoc] multiple index.html files found; "
            "using the shallowest generated site:",
            file=sys.stderr,
        )
        for index in indexes:
            print(
                f"  {index.relative_to(build_output)}",
                file=sys.stderr,
            )

    index = min(
        indexes,
        key=lambda path: len(path.relative_to(build_output).parts),
    )
    return index.parent


def main() -> int:
    """Regenerate production JavaScript API documentation with JSDoc."""
    validate_sources()

    if not CONFIG.is_file():
        raise RuntimeError(f"JSDoc configuration not found: {CONFIG}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    with tempfile.TemporaryDirectory(prefix="wg-manager-jsdoc-") as tmp:
        build_output = Path(tmp)

        command = [
            *jsdoc_command(),
            "--pedantic",
            "--verbose",
            "--configure",
            str(CONFIG),
            "--destination",
            str(build_output),
            "--package",
            str(PACKAGE_JSON),
            *map(str, SOURCE_FILES),
        ]

        print("[jsdoc]", " ".join(command), flush=True)

        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
        )

        print(f"[jsdoc] exit status: {result.returncode}", flush=True)

        if result.returncode != 0:
            print_generated_tree(build_output)
            return result.returncode

        site_root = find_site_root(build_output)

        if site_root is None:
            print(
                "[jsdoc] command succeeded but no index.html was generated",
                file=sys.stderr,
            )
            print_generated_tree(build_output)
            return 1

        print(
            "[jsdoc] generated site root: "
            f"{site_root.relative_to(build_output) or Path('.')}",
            flush=True,
        )

        shutil.copytree(site_root, OUTPUT)

    index = OUTPUT / "index.html"
    if not index.is_file():
        print(
            f"[jsdoc] normalized output is missing: {index}",
            file=sys.stderr,
        )
        print_generated_tree(OUTPUT)
        return 1

    print(
        f"[jsdoc] generated {len(SOURCE_FILES)} source modules in "
        f"{OUTPUT.relative_to(ROOT)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
