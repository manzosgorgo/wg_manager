#!/usr/bin/env python3

import opaque
import pytest

from src.wg_auth.wg_auth_account_service import WGAuthAccountService
from src.wg_auth.wg_auth_user_store import WGAuthUserStore


def test_create_and_delete_account(tmp_path):
    store = WGAuthUserStore(
        str(tmp_path),
        opaque_record_len=opaque.OPAQUE_USER_RECORD_LEN,
    )
    service = WGAuthAccountService(store)

    created = service.create("alice", "secret-password")

    assert created == {
        "username": "alice",
        "peers": [],
    }
    assert store.load("alice").username == "alice"

    deleted = service.delete("alice")

    assert deleted == {
        "username": "alice",
        "deleted": True,
    }

    with pytest.raises(FileNotFoundError):
        store.load("alice")


def test_create_account_rejects_empty_password(tmp_path):
    store = WGAuthUserStore(
        str(tmp_path),
        opaque_record_len=opaque.OPAQUE_USER_RECORD_LEN,
    )
    service = WGAuthAccountService(store)

    with pytest.raises(ValueError, match="password"):
        service.create("alice", "")
