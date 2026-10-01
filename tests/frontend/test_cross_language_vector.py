#!/usr/bin/env python3

import json
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FRONTEND_DIR = PROJECT_ROOT / "src" / "wg_frontend"

INPUT_VECTOR = FRONTEND_DIR / "wg_secure_session_vector_input.json"
CANONICAL_VECTOR = FRONTEND_DIR / "test_wg_secure_session_vectors.json"
JS_VECTOR_CHECKER = FRONTEND_DIR / "check_vectors.mjs"

PYTHON_VECTOR_GENERATOR = (
    PROJECT_ROOT / "tests" / "frontend" / "wg_secure_session_gen_vectors.py"
)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_python_generator(input_path: Path, output_path: Path) -> None:
    result = subprocess.run(
        [
            "python3",
            str(PYTHON_VECTOR_GENERATOR),
            str(input_path),
            str(output_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(
            "Python vector generator failed:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def run_js_checker() -> None:
    node = shutil.which("node")

    if node is None:
        pytest.fail("Node.js not found")

    result = subprocess.run(
        [
            node,
            str(JS_VECTOR_CHECKER),
        ],
        cwd=FRONTEND_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(
            "JavaScript vector checker failed:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def test_python_vector_matches_canonical_vector():
    with TemporaryDirectory() as tmp:
        generated_vector_path = Path(tmp) / "generated.json"

        run_python_generator(
            INPUT_VECTOR,
            generated_vector_path,
        )

        generated_vector = load_json(generated_vector_path)
        canonical_vector = load_json(CANONICAL_VECTOR)

        assert generated_vector == canonical_vector


def test_javascript_implementation_matches_canonical_vector():
    run_js_checker()