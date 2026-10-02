#!/usr/bin/env python3

import base64
import http.client
import json
import logging
import os
import socket
import ssl
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

import pytest

from src.wg_client import wg_client
from src.wg_client.wg_client_API import WGClientAPI
from src.wg_client.wg_client_errors import WGControllerError, WGProtocolError
from src.wg_client.wg_controller_client import WGControllerClient
from src.wg_client.wg_client_lifecycle import WGClientLifecycle
from src.wg_client.wg_client_IPC import WGClientIPC


log = logging.getLogger("wg_manager.test_integration")


ROOT = Path(__file__).resolve().parents[2]
CERT = ROOT / "cert"

LISTEN_PATH = "/api/7f3a91c2e8b44d17/9c71e4a2f6b83d10"

# 32 bytes whose base64 contains "/", "+" and "=".
PUBLIC_KEY = base64.b64encode(bytes([0xFB, 0xFF, 0xBF]) * 10 + b"\x00\x00").decode()

NOW = 1_800_000_000

@pytest.fixture
def lifecycle():
    return WGClientLifecycle()

@pytest.fixture
def ipc(lifecycle):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        return WGClientIPC(sock, lifecycle)
    finally:
        sock.close()


def make_config(api_port=0, controller_port=9):
    return {
        "api": {
            "host": "127.0.0.1",
            "port": api_port,
            "server_cert": str(CERT / "server.crt"),
            "server_key": str(CERT / "server.key"),
            "ca": str(CERT / "ca.crt"),
        },
        "controller": {
            "host": "127.0.0.1",
            "port": controller_port,
            "ca": str(CERT / "ca.crt"),
            "client_cert": str(CERT / "client.crt"),
            "client_key": str(CERT / "client.key"),
            "timeout": 2,
        },
        "wireguard": {
            "interface": "wg0",
        },
        "secure_session": {
            "enabled": True,
            "session_id_size": 16,
            "nonce_size": 32,
            "session_key_size": 32,
            "counter_min": 1,
            "counter_max": 0xFFFFFFFF,
        },
    }


def make_packet(**overrides):
    packet = {
        "protocol_version": 1,
        "session_id": "7f3a91c2e8b44d17a6f05c9b31de8247",
        # OPAQUE shared session secret: 64 bytes, transported as hex.
        "k_session": "ab" * 64,
        "client_id": "android-test-client",
        "principal": {"username": "alice", "peers": []},
        "timeout": 1800,
        "created_at": NOW,
        "listen_path": LISTEN_PATH,
    }
    packet.update(overrides)
    return packet


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ----------------------------------------------------------------------
# Activation packet
# ----------------------------------------------------------------------


def test_parse_activation_valid(ipc):
    activation = ipc.parse_activation(make_packet(), now=NOW + 10)

    assert activation["expires_at"] == NOW + 1800
    assert activation["listen_path"] == LISTEN_PATH
    assert activation["principal"] == {"username": "alice", "peers": []}
    assert len(activation["k_session"]) == 64
    assert len(activation["session_id"]) == 16


@pytest.mark.parametrize(
    "overrides",
    [
        {"protocol_version": 2},
        {"k_session": "not-hex"},
        {"k_session": None},
        {"k_session": "00" * 63},
        {"k_session": "00" * 65},
        {"session_id": 123},
        {"client_id": ""},
        {"principal": None},
        {"principal": {}},
        {"principal": {"username": ""}},
        {"principal": {"username": 123, "peers": []}},
        {"principal": {"username": "alice"}},
        {"principal": {"username": "alice", "peers": "not-a-list"}},
        {"principal": {"username": "alice", "peers": ["", "peer"]}},
        {"principal": {"username": "alice", "peers": ["peer", "peer"]}},
        {"listen_path": "api/no-leading-slash"},
        {"listen_path": "/api/../etc"},
        {"listen_path": "/api/trailing/"},
        {"timeout": 0},
        {"timeout": True},
        {"timeout": 10**9},
        {"created_at": "1800000000"},
        {"created_at": NOW + 3600},
        {"created_at": NOW - 3600, "timeout": 1800},
    ],
)
def test_parse_activation_rejects(overrides,ipc):
    with pytest.raises(WGProtocolError):
        ipc.parse_activation(make_packet(**overrides), now=NOW)


def run_activation(
    packet,
    cfg,
    monkeypatch,
    lifecycle,
    *,
    patch_load_config=True,
):
    """Drive wg_client.activate() over a socketpair like systemd would."""
    if patch_load_config:
        monkeypatch.setattr(wg_client, "load_config", lambda: cfg)

    monkeypatch.setattr(wg_client, "_manager_peer_snapshot", lambda api: [])
    monkeypatch.setattr(
        WGClientIPC,
        "reconcile_state",
        lambda self, peers: {"status": "OK"},
    )

    auth, client = socket.socketpair()

    try:
        ipc = WGClientIPC(client, lifecycle)

        auth.sendall(json.dumps(packet).encode() + b"\n")

        result = wg_client.activate(ipc, lifecycle)

        with auth.makefile("rb") as stream:
            reply = json.loads(stream.readline())

        return result, reply

    finally:
        auth.close()
        client.close()


def test_activation_ok_only_after_bind(monkeypatch, caplog,lifecycle,ipc):
    packet = make_packet(created_at=int(time.time()))

    with caplog.at_level(logging.DEBUG, logger="wg_manager"):
        result, reply = run_activation(
            packet,
            make_config(),
            monkeypatch,
            lifecycle
        )

    assert result is not None
    api, activation = result

    try:
        assert reply["status"] == "OK"
        assert reply["expires_at"] == activation["expires_at"]

        # The API is already bound when OK is sent.
        assert api.server is not None
        port = api.server.server_address[1]
        socket.create_connection(("127.0.0.1", port), timeout=2).close()
    finally:
        api.close()

    # k_session must never reach the logs.
    assert packet["k_session"] not in caplog.text


def test_activation_error_when_port_busy(monkeypatch,lifecycle):
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]

        packet = make_packet(created_at=int(time.time()))
        result, reply = run_activation(packet, make_config(api_port=port), monkeypatch,lifecycle)

    assert result is None
    assert reply["status"] == "ERROR"
    assert "error" in reply


def test_activation_error_on_invalid_packet(monkeypatch,lifecycle):
    result, reply = run_activation(make_packet(timeout=-1), make_config(), monkeypatch,lifecycle)

    assert result is None
    assert reply["status"] == "ERROR"


def test_activation_reports_unexpected_exception(monkeypatch, lifecycle):
    packet = make_packet(created_at=int(time.time()))

    def explode():
        raise ValueError("synthetic activation failure")

    monkeypatch.setattr(wg_client, "load_config", explode)

    result, reply = run_activation(
        packet,
        make_config(),
        monkeypatch,
        lifecycle,
        patch_load_config=False,
    )

    assert result is None
    assert reply["status"] == "ERROR"
    assert reply["error"] == "synthetic activation failure"


# ----------------------------------------------------------------------
# HTTPS API
# ----------------------------------------------------------------------


class FakeController:
    def __init__(self):
        self.calls = []
        self.status_result = {"ok": True, "interface": "wg0", "peers": []}

    def status(self):
        self.calls.append(("status",))
        return self.status_result

    def add_peer(self, public_key, allowed_ip):
        self.calls.append(("add_peer", public_key, allowed_ip))
        return {"ok": True, "public_key": public_key, "allowed_ip": allowed_ip}

    def remove_peer(self, public_key):
        self.calls.append(("remove_peer", public_key))
        return {"ok": True, "public_key": public_key}


class FakeSecureSession:
    def __init__(self):
        self.principal = {"username": "admin", "peers": []}
        self.is_admin = True

    def verify_request(self, auth, method, path, body):
        return None

    def create_response_auth(self, request_auth, status, body):
        return {
            "session_id": request_auth["session_id"],
            "counter": request_auth["counter"],
            "mac": "test-mac",
        }

    def can_access_peer(self, public_key):
        return True

    def register_peer(self, public_key):
        return None

    def unregister_peer(self, public_key):
        return None


class FakeIPC:
    def __init__(self):
        self.calls = []

    def register_peer(self, public_key, allowed_ip):
        self.calls.append(("register_peer", public_key, allowed_ip))
        return {"status": "OK"}

    def unregister_peer(self, public_key):
        self.calls.append(("unregister_peer", public_key))
        return {"status": "OK"}

    def ownership_state(self):
        self.calls.append(("ownership_state",))
        return {
            "users": ["admin", "alice"],
            "peers": [
                {
                    "public_key": PUBLIC_KEY,
                    "allowed_ip": "10.8.0.2/32",
                    "owner": "alice",
                    "ownership_state": "consistent",
                }
            ],
            "ips": {
                "10.8.0.2/32": {
                    "public_key": PUBLIC_KEY,
                    "username": "alice",
                    "ownership_state": "consistent",
                }
            },
        }

    def reassign_owner(self, public_key, username):
        self.calls.append(("reassign_owner", public_key, username))
        return {
            "public_key": public_key,
            "owner": username,
        }

    def create_user(self, username, password):
        self.calls.append(("create_user", username, password))
        return {"username": username, "peers": []}

    def delete_user(self, username):
        self.calls.append(("delete_user", username))
        return {"username": username, "deleted": True}


@pytest.fixture
def api(lifecycle):
    lifecycle.ipc = FakeIPC()
    api = WGClientAPI(
        make_config(),
        LISTEN_PATH,
        FakeSecureSession(),
        lifecycle=lifecycle,
    )
    api.controller = FakeController()
    api.peer_service.controller = api.controller
    api.bind()

    assert api.lifecycle == lifecycle
    assert lifecycle.api == api

    thread = threading.Thread(target=api.serve, daemon=True)
    thread.start()

    yield api

    api.stop()
    thread.join(timeout=5)
    assert not thread.is_alive()


def request(api, method, path, body=None, headers=None):
    headers = dict(headers or {})
    headers.setdefault("X-WG-Session-ID", "test-session")
    headers.setdefault("X-WG-Counter", "1")
    headers.setdefault("X-WG-Nonce", "test-nonce")
    headers.setdefault("X-WG-MAC", "test-mac")

    ctx = ssl.create_default_context(cafile=str(CERT / "ca.crt"))
    ctx.load_cert_chain(str(CERT / "client.crt"), str(CERT / "client.key"))

    port = api.server.server_address[1]
    conn = http.client.HTTPSConnection("127.0.0.1", port, context=ctx, timeout=5)

    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        return response.status, response.read()
    finally:
        conn.close()


def test_status_below_listen_path(api):
    status, body = request(api, "GET", LISTEN_PATH + "/v1/status")

    assert status == 200
    assert json.loads(body)["interface"] == "wg0"


def test_admin_peer_status(api):
    api.controller.status_result = {
        "ok": True,
        "interface": "wg0",
        "peers": [
            {
                "public_key": PUBLIC_KEY,
                "allowed_ips": ["10.8.0.2/32"],
            }
        ],
    }

    status, body = request(
        api,
        "GET",
        LISTEN_PATH + "/v1/admin/peers",
    )

    assert status == 200
    data = json.loads(body)
    assert data["users"] == ["admin", "alice"]
    assert data["peers"][0]["owner"] == "alice"
    assert data["peers"][0]["runtime"]["public_key"] == PUBLIC_KEY
    assert data["ips"]["10.8.0.2/32"]["public_key"] == PUBLIC_KEY


def test_admin_reassign_owner(api):
    path = (
        LISTEN_PATH
        + "/v1/admin/peers/"
        + quote(PUBLIC_KEY, safe="")
        + "/owner"
    )

    status, body = request(
        api,
        "PUT",
        path,
        body=json.dumps({"username": "alice"}),
    )

    assert status == 200
    assert json.loads(body)["owner"] == "alice"
    assert (
        "reassign_owner",
        PUBLIC_KEY,
        "alice",
    ) in api.lifecycle.ipc.calls


def test_admin_create_user(api):
    status, body = request(
        api,
        "POST",
        LISTEN_PATH + "/v1/admin/users",
        body=json.dumps({
            "username": "bob",
            "password": "secret",
        }),
    )

    assert status == 201
    assert json.loads(body)["username"] == "bob"
    assert (
        "create_user",
        "bob",
        "secret",
    ) in api.lifecycle.ipc.calls


def test_admin_delete_user(api):
    status, body = request(
        api,
        "DELETE",
        LISTEN_PATH + "/v1/admin/users/alice",
    )

    assert status == 200
    assert json.loads(body)["deleted"] is True
    assert (
        "delete_user",
        "alice",
    ) in api.lifecycle.ipc.calls


def test_outside_listen_path_is_404(api):
    status, _ = request(api, "GET", "/v1/status")

    assert status == 404
    assert api.controller.calls == []


def test_interface_mismatch_is_502(api):
    api.controller.status_result = {"ok": True, "interface": "wg1", "peers": []}

    status, _ = request(api, "GET", LISTEN_PATH + "/v1/status")

    assert status == 502


def test_put_decodes_public_key(api):
    path = LISTEN_PATH + "/v1/peers/" + quote(PUBLIC_KEY, safe="")

    status, _ = request(api, "PUT", path, body=json.dumps({"allowed_ip": "10.8.0.2/32"}))

    assert status == 200
    assert api.controller.calls == [
        ("status",),
        ("add_peer", PUBLIC_KEY, "10.8.0.2/32"),
    ]


def test_delete_decodes_public_key(api):
    path = LISTEN_PATH + "/v1/peers/" + quote(PUBLIC_KEY, safe="")

    status, _ = request(api, "DELETE", path)

    assert status == 200
    assert api.controller.calls == [("remove_peer", PUBLIC_KEY)]


def test_put_negative_content_length_is_400(api):
    path = LISTEN_PATH + "/v1/peers/" + quote(PUBLIC_KEY, safe="")

    status, _ = request(api, "PUT", path, headers={"Content-Length": "-1"})

    assert status == 400


def test_trace_not_supported(api):
    status, _ = request(api, "TRACE", LISTEN_PATH + "/v1/status")

    assert status == 501


def test_stop_before_serve_loop_does_not_hang():
    api = WGClientAPI(make_config(), LISTEN_PATH, FakeSecureSession())
    api.bind()

    # Like the session timer firing immediately.
    stopper = threading.Thread(target=api.stop, daemon=True)
    stopper.start()

    api.serve()
    stopper.join(timeout=5)

    assert not stopper.is_alive()
    assert api.server is None


# ----------------------------------------------------------------------
# Controller client
# ----------------------------------------------------------------------


def test_controller_unreachable_is_502():
    cfg = make_config(controller_port=free_port())["controller"]

    client = WGControllerClient(
        cfg["host"],
        cfg["port"],
        ca=cfg["ca"],
        cert=cfg["client_cert"],
        key=cfg["client_key"],
        timeout=cfg["timeout"],
    )

    with pytest.raises(WGControllerError) as info:
        client.status()

    assert info.value.status == 502


def test_controller_timeout_from_config():
    api = WGClientAPI(make_config(), LISTEN_PATH, FakeSecureSession())

    assert api.controller.timeout == 2


def test_api_rejects_missing_secure_session():
    with pytest.raises(RuntimeError, match="requires an authenticated secure session"):
        WGClientAPI(make_config(), LISTEN_PATH, None)


# ----------------------------------------------------------------------
# Mock
# ----------------------------------------------------------------------


def run_mock(tmp_path, *args):
    env = dict(
        os.environ,
        WG_MOCK_STATE=str(tmp_path / "state.txt"),
        WG_MOCK_LOG=str(tmp_path / "mock.log"),
    )

    return subprocess.run(
        [sys.executable, str(ROOT / "mock" / "mock"), *args],
        env=env,
        capture_output=True,
        text=True,
    )


def test_mock_handshake(tmp_path):
    assert run_mock(tmp_path, "set", "wg0", "peer", PUBLIC_KEY, "allowed-ips", "10.8.0.2/32").returncode == 0

    dump = run_mock(tmp_path, "show", "wg0", "dump").stdout.splitlines()
    assert dump[1].split("\t")[4] == "0"

    assert run_mock(tmp_path, "handshake", "wg0", PUBLIC_KEY).returncode == 0

    fields = run_mock(tmp_path, "show", "wg0", "dump").stdout.splitlines()[1].split("\t")
    assert int(fields[4]) > 0
    assert fields[2] != "(none)"


def test_mock_handshake_unknown_peer(tmp_path):
    assert run_mock(tmp_path, "handshake", "wg0", PUBLIC_KEY).returncode == 1


# ----------------------------------------------------------------------
# Persistent IPC peer ownership RPC
# ----------------------------------------------------------------------

def test_peer_register_rpc_is_completed_by_control_loop(lifecycle):
    auth_sock, client_sock = socket.socketpair()

    try:
        ipc = WGClientIPC(client_sock, lifecycle)

        thread = threading.Thread(
            target=ipc.control_loop,
            daemon=True,
        )
        thread.start()

        def responder():
            with auth_sock.makefile("rb") as stream:
                request = json.loads(stream.readline())

            assert request["type"] == "PEER_REGISTER"
            assert request["public_key"] == PUBLIC_KEY
            assert request["allowed_ip"] == "10.8.0.2/32"
            assert type(request["request_id"]) is int

            auth_sock.sendall(
                json.dumps({
                    "protocol_version": 1,
                    "type": "PEER_RESULT",
                    "request_id": request["request_id"],
                    "status": "OK",
                }).encode("utf-8") + b"\n"
            )

        responder_thread = threading.Thread(
            target=responder,
            daemon=True,
        )
        responder_thread.start()

        response = ipc.register_peer(
            PUBLIC_KEY,
            "10.8.0.2/32",
        )

        responder_thread.join(timeout=2)
        assert not responder_thread.is_alive()
        assert response["status"] == "OK"

        auth_sock.sendall(
            json.dumps({
                "protocol_version": 1,
                "type": "STOP",
            }).encode("utf-8") + b"\n"
        )

        thread.join(timeout=2)
        assert not thread.is_alive()

    finally:
        auth_sock.close()
        client_sock.close()


def test_peer_register_on_closed_ipc_is_protocol_error(lifecycle):
    auth_sock, client_sock = socket.socketpair()

    try:
        ipc = WGClientIPC(client_sock, lifecycle)
        ipc.stop(notify_shutdown=False)

        with pytest.raises(WGProtocolError, match="IPC connection is closed"):
            ipc.register_peer(
                PUBLIC_KEY,
                "10.8.0.2/32",
            )

    finally:
        auth_sock.close()



def test_manager_peer_snapshot_normalizes_controller_status():
    class API:
        interface = "wg0"
        controller = FakeController()

    API.controller.status_result = {
        "ok": True,
        "interface": "wg0",
        "peers": [
            {
                "public_key": "peer-a",
                "allowed_ips": ["10.8.0.2/32"],
            }
        ],
    }

    assert wg_client._manager_peer_snapshot(API) == [
        {
            "public_key": "peer-a",
            "allowed_ip": "10.8.0.2/32",
        }
    ]


def test_manager_peer_snapshot_rejects_ambiguous_allowed_ips():
    class API:
        interface = "wg0"
        controller = FakeController()

    API.controller.status_result = {
        "ok": True,
        "interface": "wg0",
        "peers": [
            {
                "public_key": "peer-a",
                "allowed_ips": [
                    "10.8.0.2/32",
                    "10.8.0.3/32",
                ],
            }
        ],
    }

    with pytest.raises(RuntimeError, match="cannot be reconciled safely"):
        wg_client._manager_peer_snapshot(API)
