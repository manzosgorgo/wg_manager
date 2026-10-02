#!/usr/bin/env python3

import json

import pytest

from src.wg_auth.wg_auth_peer_registry import WGAuthPeerRegistry


def test_reserve_and_release_peer(tmp_path):
    path = tmp_path / "peer-registry.json"
    registry = WGAuthPeerRegistry(str(path))

    entry = registry.reserve(
        "alice",
        "peer-a",
        "10.8.0.2/32",
    )

    assert entry == {
        "username": "alice",
        "allowed_ip": "10.8.0.2/32",
        "ownership_state": "consistent",
    }
    assert registry.get("peer-a") == entry

    released = registry.release("alice", "peer-a")

    assert released == entry
    assert registry.get("peer-a") is None


def test_duplicate_public_key_is_rejected(tmp_path):
    registry = WGAuthPeerRegistry(
        str(tmp_path / "peer-registry.json")
    )

    registry.reserve("alice", "peer-a", "10.8.0.2/32")

    with pytest.raises(ValueError, match="public key"):
        registry.reserve("bob", "peer-a", "10.8.0.3/32")


def test_duplicate_allowed_ip_is_rejected(tmp_path):
    registry = WGAuthPeerRegistry(
        str(tmp_path / "peer-registry.json")
    )

    registry.reserve("alice", "peer-a", "10.8.0.2/32")

    with pytest.raises(ValueError, match="allowed IP"):
        registry.reserve("bob", "peer-b", "10.8.0.2/32")


def test_admin_can_release_foreign_reservation(tmp_path):
    registry = WGAuthPeerRegistry(
        str(tmp_path / "peer-registry.json")
    )

    registry.reserve("alice", "peer-a", "10.8.0.2/32")

    released = registry.release("admin", "peer-a")

    assert released["username"] == "alice"


def test_non_owner_cannot_release_foreign_reservation(tmp_path):
    registry = WGAuthPeerRegistry(
        str(tmp_path / "peer-registry.json")
    )

    registry.reserve("alice", "peer-a", "10.8.0.2/32")

    with pytest.raises(PermissionError):
        registry.release("bob", "peer-a")


def test_reconcile_rebuilds_registry_from_live_state(tmp_path):
    path = tmp_path / "peer-registry.json"
    registry = WGAuthPeerRegistry(str(path))

    # Deliberately stale content.
    registry.reserve("alice", "old-peer", "10.8.0.9/32")

    result = registry.reconcile(
        [
            {
                "public_key": "peer-a",
                "allowed_ip": "10.8.0.2/32",
            },
            {
                "public_key": "peer-b",
                "allowed_ip": "10.8.0.3/32",
            },
        ],
        {
            "peer-a": "alice",
            "peer-b": "bob",
        },
    )

    assert result["peers"] == {
        "peer-a": {
            "username": "alice",
            "allowed_ip": "10.8.0.2/32",
            "ownership_state": "consistent",
        },
        "peer-b": {
            "username": "bob",
            "allowed_ip": "10.8.0.3/32",
            "ownership_state": "consistent",
        },
    }

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk == result


def test_reconcile_keeps_live_peer_without_owner_as_orphan(tmp_path):
    registry = WGAuthPeerRegistry(
        str(tmp_path / "peer-registry.json")
    )

    result = registry.reconcile(
        [
            {
                "public_key": "peer-a",
                "allowed_ip": "10.8.0.2/32",
            }
        ],
        {},
    )

    assert result["peers"]["peer-a"] == {
        "username": None,
        "allowed_ip": "10.8.0.2/32",
        "ownership_state": "orphan",
    }



def test_set_owner_repairs_orphan(tmp_path):
    registry = WGAuthPeerRegistry(
        str(tmp_path / "peer-registry.json")
    )
    registry.reconcile(
        [
            {
                "public_key": "peer-a",
                "allowed_ip": "10.8.0.2/32",
            }
        ],
        {},
    )

    updated = registry.set_owner("peer-a", "alice")

    assert updated["username"] == "alice"
    assert updated["ownership_state"] == "consistent"



def test_reserve_updates_ip_registry(tmp_path):
    peer_path = tmp_path / "peer-registry.json"
    ip_path = tmp_path / "ip-registry.json"
    registry = WGAuthPeerRegistry(
        str(peer_path),
        str(ip_path),
    )

    registry.reserve(
        "alice",
        "peer-a",
        "10.8.0.2/32",
    )

    assert registry.snapshot_ips() == {
        "10.8.0.2/32": {
            "public_key": "peer-a",
            "username": "alice",
            "ownership_state": "consistent",
        }
    }

    registry.release("alice", "peer-a")

    assert registry.snapshot_ips() == {}


def test_reconcile_rebuilds_ip_registry(tmp_path):
    registry = WGAuthPeerRegistry(
        str(tmp_path / "peer-registry.json"),
        str(tmp_path / "ip-registry.json"),
    )

    registry.reconcile(
        [
            {
                "public_key": "peer-a",
                "allowed_ip": "10.8.0.2/32",
            }
        ],
        {"peer-a": "alice"},
    )

    assert registry.snapshot_ips() == {
        "10.8.0.2/32": {
            "public_key": "peer-a",
            "username": "alice",
            "ownership_state": "consistent",
        }
    }
