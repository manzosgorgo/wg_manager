#!/usr/bin/env python3

import pytest

from src.wg_auth.wg_auth_API import WGAuthAPI
from src.wg_auth.wg_auth_errors import WGAuthSessionError


class Lifecycle:
    def __init__(self):
        self.ipc = None


class FakeSession:
    def __init__(self):
        self.logged_out = False

    def logout(self):
        self.logged_out = True


class FakeIPC:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def make_api(tmp_path):
    config = {
        "auth": {
            "login_dir": str(tmp_path),
            "peer_registry": str(tmp_path / ".peer_registry.json"),
            "ip_registry": str(tmp_path / ".ip_registry.json"),
        },
        "client": {
            "socket_path": str(tmp_path / "client.sock"),
            "client_id": "test-client",
            "timeout": "30",
            "listen_path": "/api/test",
        },
    }
    return WGAuthAPI(config, Lifecycle())


def test_finish_authentication_requires_start(tmp_path):
    api = make_api(tmp_path)

    with pytest.raises(
        WGAuthSessionError,
        match="authentication is not in progress",
    ):
        api.finish_authentication(b"auth")


def test_start_authentication_rejects_non_idle_state(tmp_path):
    api = make_api(tmp_path)
    api.session_state = api.SESSION_ACTIVE

    with pytest.raises(
        WGAuthSessionError,
        match="session already active",
    ):
        api.start_authentication("alice", b"pub")


def test_activation_failure_returns_api_to_idle(tmp_path):
    api = make_api(tmp_path)
    session = FakeSession()
    ipc = FakeIPC()

    api.session = session
    api.ipc = ipc
    api.lifecycle.ipc = ipc
    api.session_state = api.SESSION_STARTING
    api.session_stop_requested = True

    api._activation_failed(session, ipc)

    assert api.session is None
    assert api.ipc is None
    assert api.lifecycle.ipc is None
    assert api.session_state == api.SESSION_IDLE
    assert api.session_stop_requested is False
    assert session.logged_out is True
    assert ipc.closed is True


def test_logout_during_starting_defers_cleanup(tmp_path):
    api = make_api(tmp_path)
    session = FakeSession()
    ipc = FakeIPC()

    api.session = session
    api.ipc = ipc
    api.lifecycle.ipc = ipc
    api.session_state = api.SESSION_STARTING

    api.logout()

    assert api.session is session
    assert api.ipc is ipc
    assert api.session_state == api.SESSION_STOPPING
    assert api.session_stop_requested is True
    assert session.logged_out is False
    assert ipc.closed is False
