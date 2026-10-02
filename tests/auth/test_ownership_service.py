#!/usr/bin/env python3

from src.wg_auth.wg_auth_ownership_service import WGAuthOwnershipService
from src.wg_auth.wg_auth_peer_registry import WGAuthPeerRegistry
from src.wg_auth.wg_auth_user_store import WGAuthUserStore


def make_service(tmp_path):
    store = WGAuthUserStore(str(tmp_path))
    registry = WGAuthPeerRegistry(
        str(tmp_path / ".peer_registry.json")
    )
    return store, registry, WGAuthOwnershipService(store, registry)


def test_admin_state_reports_orphan_and_stale(tmp_path):
    store, registry, service = make_service(tmp_path)

    store.create_user("alice", b"A" * 256)
    store.create_user("bob", b"B" * 256)
    store.add_peer("alice", "stale-peer")

    registry.reconcile(
        [
            {
                "public_key": "orphan-peer",
                "allowed_ip": "10.8.0.2/32",
            }
        ],
        store.peer_owners(),
    )

    state = service.admin_state()
    peers = {
        peer["public_key"]: peer
        for peer in state["peers"]
    }

    assert state["users"] == ["alice", "bob"]
    assert peers["orphan-peer"]["owner"] is None
    assert peers["orphan-peer"]["ownership_state"] == "orphan"
    assert peers["stale-peer"]["owner"] == "alice"
    assert peers["stale-peer"]["ownership_state"] == "stale"


def test_reassign_claims_orphan_peer(tmp_path):
    store, registry, service = make_service(tmp_path)

    store.create_user("alice", b"A" * 256)
    registry.reconcile(
        [
            {
                "public_key": "peer-a",
                "allowed_ip": "10.8.0.2/32",
            }
        ],
        {},
    )

    result = service.reassign("peer-a", "alice")

    assert result == {
        "public_key": "peer-a",
        "owner": "alice",
    }
    assert store.load("alice").peers == ("peer-a",)
    assert registry.get("peer-a")["username"] == "alice"
    assert registry.get("peer-a")["ownership_state"] == "consistent"


def test_reassign_moves_peer_between_users(tmp_path):
    store, registry, service = make_service(tmp_path)

    store.create_user("alice", b"A" * 256)
    store.create_user("bob", b"B" * 256)
    store.add_peer("alice", "peer-a")
    registry.reconcile(
        [
            {
                "public_key": "peer-a",
                "allowed_ip": "10.8.0.2/32",
            }
        ],
        store.peer_owners(),
    )

    service.reassign("peer-a", "bob")

    assert store.load("alice").peers == ()
    assert store.load("bob").peers == ("peer-a",)
    assert registry.get("peer-a")["username"] == "bob"
