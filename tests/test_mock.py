#!/usr/bin/env python3

import base64
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MOCK_PROGRAM = ROOT / "mock" / "mock"
REAL_WG_PATHS = {
    Path("/usr/bin/wg"),
    Path("/usr/local/bin/wg"),
}

PUBLIC_KEY = base64.b64encode(b"mock-test-public-key-32-bytes!!").decode()
SECOND_PUBLIC_KEY = base64.b64encode(b"mock-test-public-key-2-32-byte!!").decode()


@pytest.fixture(scope="session", autouse=True)
def verify_mock_executable():
    """
    Safety preflight.

    This must succeed before any test is allowed to invoke a subprocess.
    The tests intentionally execute only the repository mock and never a
    system WireGuard executable.
    """
    expected = MOCK_PROGRAM.resolve()

    assert expected.is_file(), f"mock executable does not exist: {expected}"
    assert os.access(expected, os.X_OK), f"mock is not executable: {expected}"
    assert expected not in {path.resolve() for path in REAL_WG_PATHS}, (
        f"refusing to run a real WireGuard executable: {expected}"
    )

    # Content check makes the path check robust against an accidentally
    # replaced/symlinked test target.
    content = expected.read_text()
    assert "WG_MOCK_STATE" in content
    assert "def show(interface):" in content
    assert "def set_peer(args):" in content
    assert "def handshake(args):" in content


@pytest.fixture
def mock_env(tmp_path):
    return {
        **os.environ,
        "WG_MOCK_STATE": str(tmp_path / "state.txt"),
        "WG_MOCK_LOG": str(tmp_path / "mock.log"),
    }


def run_mock(mock_env, *args):
    # Do not resolve this dynamically from PATH or WG_PROGRAM: the executable
    # is deliberately fixed to the repository mock after the safety preflight.
    return subprocess.run(
        [str(MOCK_PROGRAM), *args],
        env=mock_env,
        capture_output=True,
        text=True,
        check=False,
    )


def dump_peers(mock_env):
    result = run_mock(mock_env, "show", "wg0", "dump")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    return [line.split("\t") for line in lines[1:]]


def test_initial_state_is_empty(mock_env):
    result = run_mock(mock_env, "show", "wg0", "dump")

    assert result.returncode == 0
    assert result.stderr == ""

    lines = result.stdout.splitlines()
    assert len(lines) == 1
    assert lines[0].split("\t") == [
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "51820",
        "off",
    ]


def test_add_peer(mock_env):
    result = run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        PUBLIC_KEY,
        "allowed-ips",
        "10.8.0.2/32",
    )

    assert result.returncode == 0
    assert result.stderr == ""

    peers = dump_peers(mock_env)
    assert len(peers) == 1
    assert peers[0][0] == PUBLIC_KEY
    assert peers[0][3] == "10.8.0.2/32"
    assert peers[0][4:] == ["0", "0", "0", "0"]


def test_update_peer(mock_env):
    add = run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        PUBLIC_KEY,
        "allowed-ips",
        "10.8.0.2/32",
    )
    assert add.returncode == 0

    update = run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        PUBLIC_KEY,
        "allowed-ips",
        "10.8.0.99/32",
    )
    assert update.returncode == 0

    peers = dump_peers(mock_env)
    assert len(peers) == 1
    assert peers[0][0] == PUBLIC_KEY
    assert peers[0][3] == "10.8.0.99/32"


def test_remove_peer(mock_env):
    assert run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        PUBLIC_KEY,
        "allowed-ips",
        "10.8.0.2/32",
    ).returncode == 0

    result = run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        PUBLIC_KEY,
        "remove",
    )

    assert result.returncode == 0
    assert dump_peers(mock_env) == []


def test_remove_unknown_peer_fails(mock_env):
    result = run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        PUBLIC_KEY,
        "remove",
    )

    assert result.returncode == 1
    assert "peer not found" in result.stderr
    assert dump_peers(mock_env) == []


@pytest.mark.parametrize(
    "args",
    [
        ("show", "wg1", "dump"),
        ("set", "wg1", "peer", PUBLIC_KEY, "allowed-ips", "10.8.0.2/32"),
        ("set", "wg0", "peer", "not-a-wireguard-key", "allowed-ips", "10.8.0.2/32"),
        ("set", "wg0", "peer", PUBLIC_KEY, "unsupported", "10.8.0.2/32"),
    ],
)
def test_invalid_commands_are_rejected(mock_env, args):
    result = run_mock(mock_env, *args)

    assert result.returncode == 1
    assert result.stderr.startswith("mock:")


def test_handshake_updates_peer_statistics(mock_env):
    assert run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        PUBLIC_KEY,
        "allowed-ips",
        "10.8.0.2/32",
    ).returncode == 0

    before = dump_peers(mock_env)
    assert before[0][2] == "(none)"
    assert before[0][4:] == ["0", "0", "0", "0"]

    result = run_mock(
        mock_env,
        "handshake",
        "wg0",
        PUBLIC_KEY,
        "192.0.2.20:51820",
    )

    assert result.returncode == 0

    after = dump_peers(mock_env)
    assert after[0][0] == PUBLIC_KEY
    assert after[0][2] == "192.0.2.20:51820"
    assert int(after[0][4]) > 0
    assert after[0][5] == "1024"
    assert after[0][6] == "1024"


def test_state_persists_between_invocations(mock_env):
    assert run_mock(
        mock_env,
        "set",
        "wg0",
        "peer",
        SECOND_PUBLIC_KEY,
        "allowed-ips",
        "10.8.0.3/32",
    ).returncode == 0

    state_file = Path(mock_env["WG_MOCK_STATE"])
    assert state_file.is_file()

    result = run_mock(mock_env, "show", "wg0", "dump")
    assert result.returncode == 0

    peers = dump_peers(mock_env)
    assert len(peers) == 1
    assert peers[0][0] == SECOND_PUBLIC_KEY
    assert peers[0][3] == "10.8.0.3/32"
