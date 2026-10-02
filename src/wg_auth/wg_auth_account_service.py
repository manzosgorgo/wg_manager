#!/usr/bin/env python3

import opaque


SERVER_ID = b"wg-auth"


class WGAuthAccountService:
    """Administrative account lifecycle and OPAQUE record creation."""

    def __init__(self, user_store):
        self.user_store = user_store

    @staticmethod
    def make_opaque_record(username, password):
        if not isinstance(username, str) or not username:
            raise ValueError("username must be a non-empty string")
        if not isinstance(password, str) or not password:
            raise ValueError("password must be a non-empty string")

        ids = opaque.Ids(
            username.encode("utf-8"),
            SERVER_ID,
        )

        sec_u, request = opaque.CreateRegistrationRequest(
            password.encode("utf-8")
        )
        sec_s, response = opaque.CreateRegistrationResponse(request)
        rec0, _export_key = opaque.FinalizeRequest(
            sec_u,
            response,
            ids,
        )
        record = opaque.StoreUserRecord(sec_s, rec0)

        if len(record) != opaque.OPAQUE_USER_RECORD_LEN:
            raise RuntimeError(
                f"unexpected OPAQUE record size: {len(record)}"
            )

        return record

    def create(self, username, password):
        record = self.make_opaque_record(
            username,
            password,
        )
        user = self.user_store.create_user(
            username,
            record,
        )
        return {
            "username": user.username,
            "peers": list(user.peers),
        }

    def delete(self, username):
        self.user_store.delete_user(username)
        return {
            "username": username,
            "deleted": True,
        }
