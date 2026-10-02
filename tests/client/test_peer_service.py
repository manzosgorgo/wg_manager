#!/usr/bin/env python3

import pytest

from src.wg_client.wg_client_errors import (
    WGControllerError,
    WGPeerError,
    WGPeerPersistenceError,
)
from src.wg_client.wg_peer_service import WGPeerService


class FakeSession:
    def __init__(self, username="alice", peers=(), admin=False):
        self.principal = {
            "username": username,
            "peers": list(peers),
        }
        self._peers = set(peers)
        self.is_admin = admin

    def can_access_peer(self, public_key):
        return self.is_admin or public_key in self._peers

    def register_peer(self, public_key):
        self._peers.add(public_key)

    def unregister_peer(self, public_key):
        self._peers.discard(public_key)


class FakeIPC:
    def __init__(self):
        self.calls = []
        self.ownership = {
            "users": ["admin", "alice"],
            "peers": [],
        }

    def register_peer(self, public_key, allowed_ip):
        self.calls.append(("register", public_key, allowed_ip))

    def unregister_peer(self, public_key):
        self.calls.append(("unregister", public_key))

    def ownership_state(self):
        self.calls.append(("ownership_state",))
        return self.ownership

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


class FakeLifecycle:
    def __init__(self):
        self.ipc = FakeIPC()


class FakeController:
    def __init__(self):
        self.calls = []
        self.status_result = {
            "ok": True,
            "interface": "wg0",
            "peers": [],
        }
        self.add_error = None

    def status(self):
        self.calls.append(("status",))
        return self.status_result

    def add_peer(self, public_key, allowed_ip):
        self.calls.append(("add", public_key, allowed_ip))
        if self.add_error is not None:
            raise self.add_error
        return {
            "ok": True,
            "public_key": public_key,
            "allowed_ip": allowed_ip,
        }

    def remove_peer(self, public_key):
        self.calls.append(("remove", public_key))
        return {"ok": True, "public_key": public_key}


def test_status_filters_foreign_peers():
    session = FakeSession(peers=("mine",))
    controller = FakeController()
    controller.status_result["peers"] = [
        {"public_key": "mine"},
        {"public_key": "foreign"},
    ]

    service = WGPeerService(
        controller,
        session,
        FakeLifecycle(),
        "wg0",
    )

    result = service.status()

    assert result["peers"] == [{"public_key": "mine"}]


def test_remove_foreign_peer_is_forbidden():
    service = WGPeerService(
        FakeController(),
        FakeSession(peers=()),
        FakeLifecycle(),
        "wg0",
    )

    with pytest.raises(WGPeerError) as info:
        service.remove_peer("foreign")

    assert info.value.status == 403


def test_add_rolls_back_ownership_when_controller_fails():
    controller = FakeController()
    controller.add_error = WGControllerError(
        409,
        "duplicate public key",
    )
    lifecycle = FakeLifecycle()
    session = FakeSession()

    service = WGPeerService(
        controller,
        session,
        lifecycle,
        "wg0",
    )

    with pytest.raises(WGPeerError) as info:
        service.add_peer("peer-a", "10.8.0.2/32")

    assert info.value.status == 409
    assert lifecycle.ipc.calls == [
        ("register", "peer-a", "10.8.0.2/32"),
        ("unregister", "peer-a"),
    ]
    assert not session.can_access_peer("peer-a")


def test_add_updates_session_only_after_controller_success():
    controller = FakeController()
    lifecycle = FakeLifecycle()
    session = FakeSession()

    service = WGPeerService(
        controller,
        session,
        lifecycle,
        "wg0",
    )

    result = service.add_peer("peer-a", "10.8.0.2/32")

    assert result["ok"] is True
    assert lifecycle.ipc.calls == [
        ("register", "peer-a", "10.8.0.2/32")
    ]
    assert session.can_access_peer("peer-a")



def test_registry_conflict_is_preserved_as_409():
    class ConflictIPC(FakeIPC):
        def register_peer(self, public_key, allowed_ip):
            raise WGPeerPersistenceError(
                409,
                "allowed IP is already reserved",
            )

    lifecycle = FakeLifecycle()
    lifecycle.ipc = ConflictIPC()

    service = WGPeerService(
        FakeController(),
        FakeSession(),
        lifecycle,
        "wg0",
    )

    with pytest.raises(WGPeerError) as info:
        service.add_peer("peer-b", "10.8.0.2/32")

    assert info.value.status == 409


def test_existing_owned_key_is_rejected_before_reservation():
    controller = FakeController()
    controller.status_result["peers"] = [
        {"public_key": "peer-a"},
    ]
    lifecycle = FakeLifecycle()
    session = FakeSession(peers=("peer-a",))

    service = WGPeerService(
        controller,
        session,
        lifecycle,
        "wg0",
    )

    with pytest.raises(WGPeerError) as info:
        service.add_peer("peer-a", "10.8.0.2/32")

    assert info.value.status == 409
    assert lifecycle.ipc.calls == []



def test_admin_status_merges_runtime_and_ownership():
    controller = FakeController()
    controller.status_result["peers"] = [
        {
            "public_key": "peer-a",
            "allowed_ips": ["10.8.0.2/32"],
        }
    ]
    lifecycle = FakeLifecycle()
    lifecycle.ipc.ownership = {
        "users": ["admin", "alice"],
        "peers": [
            {
                "public_key": "peer-a",
                "allowed_ip": "10.8.0.2/32",
                "owner": None,
                "ownership_state": "orphan",
            }
        ],
    }

    service = WGPeerService(
        controller,
        FakeSession(username="admin", admin=True),
        lifecycle,
        "wg0",
    )

    result = service.admin_status()

    assert result["users"] == ["admin", "alice"]
    assert result["peers"][0]["ownership_state"] == "orphan"
    assert result["peers"][0]["runtime"]["public_key"] == "peer-a"


def test_non_admin_cannot_read_admin_status():
    service = WGPeerService(
        FakeController(),
        FakeSession(username="alice"),
        FakeLifecycle(),
        "wg0",
    )

    with pytest.raises(WGPeerError) as info:
        service.admin_status()

    assert info.value.status == 403


def test_admin_can_reassign_owner():
    lifecycle = FakeLifecycle()
    service = WGPeerService(
        FakeController(),
        FakeSession(username="admin", admin=True),
        lifecycle,
        "wg0",
    )

    result = service.reassign_owner("peer-a", "alice")

    assert result["owner"] == "alice"
    assert lifecycle.ipc.calls == [
        ("reassign_owner", "peer-a", "alice"),
    ]



def test_admin_can_create_user():
    lifecycle = FakeLifecycle()
    service = WGPeerService(
        FakeController(),
        FakeSession(username="admin", admin=True),
        lifecycle,
        "wg0",
    )

    result = service.create_user("bob", "secret")

    assert result["username"] == "bob"
    assert lifecycle.ipc.calls == [
        ("create_user", "bob", "secret"),
    ]


def test_admin_cannot_delete_active_account():
    service = WGPeerService(
        FakeController(),
        FakeSession(username="admin", admin=True),
        FakeLifecycle(),
        "wg0",
    )

    with pytest.raises(WGPeerError) as info:
        service.delete_user("admin")

    assert info.value.status == 409
