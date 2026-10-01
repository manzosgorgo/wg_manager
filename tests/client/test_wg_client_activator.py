#!/usr/bin/env python3
import subprocess
import threading
import time
from asyncio import futures

import pytest

from src.wg_client.wg_client_activator import activate_client


DEFAULT_SOCKET = "/run/wg_manager/wg-client-test.sock"


@pytest.fixture
def activation_params():
    return {
        "socket_path": DEFAULT_SOCKET,
        "k_sess": (
            "b7e4a2c91f6d0835"
            "9a31c7e4b25f608d"
            "4c8e1a73f0b692de"
            "5a17c3f84e29b601"
        ),
        "timeout": 30,
        "client_id": "pytest-client",
        "principal": {"username": "pytest-user"},
        "session_id": "7f3a91c2e8b44d17a6f05c9b31de8247",
        "listen_path": "/api/7f3a91c2e8b44d17/9c71e4a2f6b83d10",
    }
def systemd_client_instances():
    result = subprocess.run(
        [
            "systemctl",
            "list-units",
            "--all",
            "--no-legend",
            "--plain",
            "wg-client-test@*.service",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return {
        line.split()[0]
        for line in result.stdout.splitlines()
        if line.strip()
    }

def systemd_session_units(session_id):
    units = systemd_client_instances()

    found = set()

    for unit in units:
        result = subprocess.run(
            [
                "systemctl",
                "show",
                unit,
                "--property=StatusText",
                "--value",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip() == f"session_id={session_id}":
            found.add(unit)

    return found

def wait_until(predicate, timeout=5, interval=0.1):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)

    return False

def test_activation(activation_params):
    with activate_client(**activation_params) as session:
        assert session.response["status"] == "OK"

def test_activation_invalid(activation_params):
    params = activation_params.copy()
    params["session_id"] = "invalid-session-id"

    with activate_client(**params) as session:
        assert session.response["status"] == "ERROR"

def test_activation_timeout(activation_params):
    params = activation_params.copy()
    params["timeout"] = 2
    session = activate_client(**params)

    try:
        assert session.response["status"] == "OK"

        def session_exists():
            return bool(
                systemd_session_units(params["session_id"])
            )

        wait_until(session_exists, timeout=5)

        assert not session_exists()

    finally:
        session.close()


from concurrent.futures import ThreadPoolExecutor


def test_concurrent_activation(activation_params):
    params_a = activation_params.copy()
    params_b = activation_params.copy()

    params_a["session_id"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    params_b["session_id"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    params_a["client_id"] = "pytest-client-a"
    params_b["client_id"] = "pytest-client-b"

    sessions = []

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(activate_client, **params_a),
                executor.submit(activate_client, **params_b),
            ]

            sessions = [
                future.result()
                for future in futures
            ]

        assert sum(
            session.response["status"] == "OK"
            for session in sessions
        ) == 1

        assert sum(
            session.response["status"] == "ERROR"
            for session in sessions
        ) == 1

        assert sessions[0].sock is not sessions[1].sock

    finally:
        for session in sessions:
            session.close()