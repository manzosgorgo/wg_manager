#!/usr/bin/env python3
"""Generate JSDoc HTML for the production frontend under docs/ai/jsdoc."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys


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


def main() -> int:
    """Regenerate production JavaScript API documentation with JSDoc."""
    validate_sources()

    if not CONFIG.is_file():
        raise RuntimeError(f"JSDoc configuration not found: {CONFIG}")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    command = [
        *jsdoc_command(),
        "--pedantic",
        "--configure",
        str(CONFIG),
        "--destination",
        str(OUTPUT),
        "--package",
        str(PACKAGE_JSON),
        *map(str, SOURCE_FILES),
    ]

    print("[jsdoc]", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
    )

    if result.returncode != 0:
        return result.returncode

    index = OUTPUT / "index.html"
    if not index.is_file():
        print(
            f"[jsdoc] expected output was not generated: {index}",
            file=sys.stderr,
        )
        return 1

    print(
        f"[jsdoc] generated {len(SOURCE_FILES)} source modules in "
        f"{OUTPUT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
