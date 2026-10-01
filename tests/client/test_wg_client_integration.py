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
        "principal": {"username": "alice"},
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
    assert activation["principal"] == {"username": "alice"}
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
        {"principal": {"username": 123}},
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


def run_activation(packet, cfg, monkeypatch,lifecycle):
    """Drive wg_client.activate() over a socketpair like systemd would."""
    monkeypatch.setattr(wg_client, "load_config", lambda: cfg)

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


@pytest.fixture
def api(lifecycle):
    api = WGClientAPI(
        make_config(),
        LISTEN_PATH,
        lifecycle=lifecycle)
    api.controller = FakeController()
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
    ctx = ssl.create_default_context(cafile=str(CERT / "ca.crt"))
    ctx.load_cert_chain(str(CERT / "client.crt"), str(CERT / "client.key"))

    port = api.server.server_address[1]
    conn = http.client.HTTPSConnection("127.0.0.1", port, context=ctx, timeout=5)

    try:
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        return response.status, response.read()
    finally:
        conn.close()


def test_status_below_listen_path(api):
    status, body = request(api, "GET", LISTEN_PATH + "/v1/status")

    assert status == 200
    assert json.loads(body)["interface"] == "wg0"


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
    assert api.controller.calls == [("add_peer", PUBLIC_KEY, "10.8.0.2/32")]


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
    api = WGClientAPI(make_config(), LISTEN_PATH)
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
    api = WGClientAPI(make_config(), LISTEN_PATH)

    assert api.controller.timeout == 2


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
