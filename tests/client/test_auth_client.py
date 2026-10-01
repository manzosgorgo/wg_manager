#!/usr/bin/env python3

import base64
import ipaddress
from typing import Any
from unittest import result

import pytest

from src.wg_client import wg_client_config
from src.wg_client.wg_client_activator import activate_client
from src.wg_client.wg_controller_client import WGClientClient
from src.wg_client.wg_client_errors import WGControllerError
from src.wg_client.wg_secure_session import WGSecureSession
from pathlib import Path

CLIENT_CONFIG = Path("../../config/wg-client-test-auth.conf")


def set_secure_session(enabled: bool):
    text = CLIENT_CONFIG.read_text()

    old = "enabled = true" if not enabled else "enabled = false"
    new = "enabled = true" if enabled else "enabled = false"

    if old not in text:
        return

    CLIENT_CONFIG.write_text(text.replace(old, new, 1))


@pytest.fixture
def secure_session_config():
    original = CLIENT_CONFIG.read_text()

    yield

    CLIENT_CONFIG.write_text(original)

@pytest.fixture(autouse=True)
def configure_client():
    set_secure_session(True)
def make_key(value):
    """
    Genera una public key WireGuard fittizia ma sintatticamente valida.
    """
    data = bytes([value]) * 32
    return base64.b64encode(data).decode()


def expect_error(func, status, message):
    try:
        func()
    except WGControllerError as ee:
        assert ee.status == status, f"{message} -> HTTP {ee.status}"
        return

    raise AssertionError(
        f"{message} -> expected HTTP {status}"
    )

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
        "session_id": "7f3a91c2e8b44d17a6f05c9b31de8247",
        "listen_path": "/api/7f3a91c2e8b44d17/9c71e4a2f6b83d10",
    }
@pytest.fixture
def client(activation_params):
    k_session = bytes.fromhex(activation_params["k_sess"])
    session_id = bytes.fromhex(activation_params["session_id"])

    session = WGSecureSession(
        wg_client_config.load_config(),
        k_session,
        session_id,
    )

    return WGClientClient(
        host="127.0.0.1",
        port=9444,
        ca=str("../../cert/ca.crt"),
        cert=str("../../cert/client.crt"),
        key=str("../../cert/client.key"),
        listen_path="/api/7f3a91c2e8b44d17/9c71e4a2f6b83d10",
        secure_session=session,
    )
@pytest.fixture
def peer_data():
    key1 = make_key(1)
    key2 = make_key(2)
    key3 = make_key(3)
    key4 = make_key(4)

    ip1 = "10.8.0.2/32"
    ip2 = "10.8.0.3/32"
    ip3 = "10.8.0.4/32"
    ip4 = "10.8.0.5/32"

    return key1, key2, key3, key4, ip1, ip2, ip3, ip4

def test_params(client, peer_data,activation_params):
    with activate_client(**activation_params) as session:
        vpn_network = "10.8.0.0/24"
        keys = [0,0,0,0]
        ips = [0,0,0,0]
        keys[0],keys[1],keys[2],keys[3],ips[0],ips[1],ips[2],ips[3] = peer_data

    #    ips_str = [str(ipaddress.ip_interface(ip)) for ip in ips]
        vpn_network = ipaddress.ip_network(
            vpn_network,
            strict=False
        )

        ips_obj = [ipaddress.ip_interface(ip) for ip in ips]
        for i in ips_obj:
            assert i.ip in vpn_network
            assert i.network.prefixlen == 32


def test_remove_peer(client: WGClientClient, peer_data,activation_params):
    with activate_client(**activation_params) as session:

        _,_,_,key1,_,_,_,ip1 = peer_data
        expect_error(
            lambda: client.remove_peer(key1),
            404,
            "removing non-existing peer rejected"
        )
        result_add = client.add_peer(key1, ip1)
        assert result_add.get("ok") is True

        result_remove = client.remove_peer(key1)
        assert result_remove.get("ok") is True, "remove peer"
        assert isinstance(result_remove.get("public_key"), str), "returned public key is string"
        # assert result.get("public_key") == key1, "returned public key is correct"
        # assert result.get("allowed_ip") == ip1, "returned allowed IP is correct"

        status = client.status()

        assert isinstance(status.get("peers"), list), "status contains peer list"
        assert not any(
            p["public_key"] == key1
            for p in status["peers"]
        ), "peer disappeared from status"


def test_add_peer_errors(client: WGClientClient, peer_data,activation_params):
    with activate_client(**activation_params) as session:
        _,key1,key2,_,_,ip1,ip2,_ = peer_data
        expect_error(
            lambda: client.add_peer(key1, ip2),
            409,
            "duplicate public key rejected"
        )

        # ------------------------------------------------------------------
        # 5. DUPLICATE IP
        # ------------------------------------------------------------------

        expect_error(
            lambda: client.add_peer(key2, ip1),
            409,
            "duplicate allowed IP rejected"
        )

        # ------------------------------------------------------------------
        # 6. INVALID PUBLIC KEY
        # ------------------------------------------------------------------

        expect_error(
            lambda: client.add_peer(
                "this-is-not-a-wireguard-key",
                ip2
            ),
            400,
            "invalid public key rejected"
        )

        # ------------------------------------------------------------------
        # 7. INVALID IP
        # ------------------------------------------------------------------

        expect_error(
            lambda: client.add_peer(
                key2,
                "not-an-ip"
            ),
            400,
            "invalid IP rejected"
        )

        # ------------------------------------------------------------------
        # 8. OUTSIDE VPN NETWORK
        # ------------------------------------------------------------------

        outside = "192.0.2.1/32"

        expect_error(
            lambda: client.add_peer(
                key2,
                outside
            ),
            400,
            "IP outside VPN network rejected"
        )


def test_add_peer_and_verify(client: WGClientClient, peer_data,activation_params):
    with activate_client(**activation_params) as session:
        key1,_,_,_,ip1,_,_,_ = peer_data
        try:
            result = client.add_peer(
                key1,
                ip1
            )

            assert result.get("ok") is True, "add first peer"
            assert isinstance(result.get("public_key"), str), "returned public key is string"
            assert result.get("public_key") == key1, "returned public key is correct"
            assert result.get("allowed_ip") == ip1, "returned allowed IP is correct"

            status = client.status()
            peers = status["peers"]

            assert isinstance(peers, list), "status contains peer list"
            assert any(
                p["public_key"] == key1
                for p in peers
            ), "peer appears in status"
        finally:
            client.remove_peer(key1)

def test_authenticated_status(activation_params,client ):
    with activate_client(**activation_params) as session:
        result = client.status()

        assert result["ok"] is True
        assert isinstance(result["peers"], list)
