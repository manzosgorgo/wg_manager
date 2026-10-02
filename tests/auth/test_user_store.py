#!/usr/bin/env python3

import base64
import json

from src.wg_auth.wg_auth_user_store import WGAuthUserStore


def make_user_file(tmp_path, username="alice"):
    record = {
        "opaque_record": base64.b64encode(b"A" * 256).decode("ascii"),
        "peers": [],
    }

    path = tmp_path / username
    path.write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    return path


def test_add_and_remove_peer_are_persistent(tmp_path):
    path = make_user_file(tmp_path)
    store = WGAuthUserStore(str(tmp_path))

    store.add_peer("alice", "peer-a")

    loaded = store.load("alice")
    assert loaded.peers == ("peer-a",)

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["peers"] == ["peer-a"]

    store.remove_peer("alice", "peer-a")

    loaded = store.load("alice")
    assert loaded.peers == ()

    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["peers"] == []


def test_add_peer_is_idempotent(tmp_path):
    make_user_file(tmp_path)
    store = WGAuthUserStore(str(tmp_path))

    store.add_peer("alice", "peer-a")
    store.add_peer("alice", "peer-a")

    assert store.load("alice").peers == ("peer-a",)


def test_remove_missing_peer_is_idempotent(tmp_path):
    make_user_file(tmp_path)
    store = WGAuthUserStore(str(tmp_path))

    store.remove_peer("alice", "peer-a")

    assert store.load("alice").peers == ()



def test_create_and_delete_user(tmp_path):
    store = WGAuthUserStore(str(tmp_path))

    user = store.create_user(
        "bob",
        b"B" * 256,
    )

    assert user.username == "bob"
    assert user.peers == ()
    assert store.load("bob").credential_record == b"B" * 256

    store.delete_user("bob")

    assert not (tmp_path / "bob").exists()


def test_create_user_is_exclusive(tmp_path):
    store = WGAuthUserStore(str(tmp_path))

    store.create_user("bob", b"B" * 256)

    import pytest
    with pytest.raises(FileExistsError):
        store.create_user("bob", b"C" * 256)


def test_delete_user_with_owned_peers_is_rejected(tmp_path):
    store = WGAuthUserStore(str(tmp_path))
    store.create_user("bob", b"B" * 256)
    store.add_peer("bob", "peer-a")

    import pytest
    with pytest.raises(ValueError, match="owned peers"):
        store.delete_user("bob")

    assert (tmp_path / "bob").exists()
