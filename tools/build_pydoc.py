#!/usr/bin/env python3
"""Generate pydoc HTML for the Python implementation under docs/ai/pydoc."""

from __future__ import annotations

import html
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "docs" / "ai" / "pydoc"

PACKAGES = (
    SRC / "wg_auth",
    SRC / "wg_client",
    SRC / "wg_manager",
)


def discover_modules():
    modules = []

    for package_dir in PACKAGES:
        package = package_dir.name

        for path in sorted(package_dir.glob("*.py")):
            if path.name == "__init__.py":
                continue

            modules.append(f"src.{package}.{path.stem}")

    return modules


def build_environment():
    env = os.environ.copy()

    python_path = [
        str(ROOT),
        str(SRC / "wg_auth"),
        str(SRC / "wg_client"),
    ]

    current = env.get("PYTHONPATH")
    if current:
        python_path.append(current)

    env["PYTHONPATH"] = os.pathsep.join(python_path)
    env.setdefault(
        "WG_CONFIG",
        str(ROOT / "config" / "wg-manager.conf"),
    )

    return env


def output_filename(module):
    return f"{module}.html"


def generate_module(module, env):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pydoc",
            "-w",
            module,
        ],
        cwd=OUTPUT,
        env=env,
        capture_output=True,
        text=True,
    )

    return result


def write_index(successes, failures):
    groups = {}

    for module in successes:
        package = module.split(".")[1]
        groups.setdefault(package, []).append(module)

    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>wg_manager Python API</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;line-height:1.5}",
        "code{background:#f3f3f3;padding:.1em .3em;border-radius:4px}",
        "li{margin:.35em 0}",
        ".error{color:#a00}",
        "</style>",
        "</head>",
        "<body>",
        "<h1>wg_manager Python API</h1>",
        "<p>Generated with <code>pydoc</code> from the current Python source tree.</p>",
    ]

    for package in ("wg_auth", "wg_client", "wg_manager"):
        modules = groups.get(package, [])
        if not modules:
            continue

        parts.append(f"<h2>{html.escape(package)}</h2>")
        parts.append("<ul>")

        for module in modules:
            filename = output_filename(module)
            parts.append(
                f'<li><a href="{html.escape(filename)}">'
                f"{html.escape(module)}</a></li>"
            )

        parts.append("</ul>")

    if failures:
        parts.append("<h2>Generation errors</h2>")
        parts.append(
            "<p class=\"error\">These modules could not be imported by pydoc.</p>"
        )
        parts.append("<ul>")

        for module, error in failures:
            parts.append(
                "<li><code>"
                + html.escape(module)
                + "</code>: "
                + html.escape(error)
                + "</li>"
            )

        parts.append("</ul>")

    parts.extend([
        "</body>",
        "</html>",
        "",
    ])

    (OUTPUT / "index.html").write_text(
        "\n".join(parts),
        encoding="utf-8",
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for old in OUTPUT.glob("*.html"):
        old.unlink()

    env = build_environment()
    successes = []
    failures = []

    for module in discover_modules():
        print(f"[pydoc] {module}")
        result = generate_module(module, env)

        expected = OUTPUT / output_filename(module)

        if result.returncode == 0 and expected.exists():
            successes.append(module)
            continue

        error = (
            result.stderr.strip()
            or result.stdout.strip()
            or "pydoc did not create the expected HTML file"
        )
        failures.append((module, error))

    write_index(successes, failures)

    print(
        f"[pydoc] generated {len(successes)} modules in "
        f"{OUTPUT.relative_to(ROOT)}"
    )

    if failures:
        print(f"[pydoc] {len(failures)} module(s) failed", file=sys.stderr)
        for module, error in failures:
            print(f"  {module}: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
