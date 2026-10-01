#!/usr/bin/env python3

import base64
import binascii
import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WGAuthUser:
    username: str
    credential_record: bytes
    peers: tuple[str, ...]

    @property
    def principal(self):
        return {"username": self.username, "peers": list(self.peers)}


class WGAuthUserStore:
    """Persistent OPAQUE credentials and peer ownership records."""

    def __init__(self, login_dir, opaque_record_len=256):
        self.login_dir = login_dir
        self.opaque_record_len = opaque_record_len

    def _path(self, username):
        if (
            not isinstance(username, str)
            or not username
            or username in (".", "..")
            or os.path.basename(username) != username
            or "/" in username
            or "\\" in username
        ):
            raise ValueError("invalid username")

        return os.path.join(self.login_dir, username)

    def load(self, username):
        path = self._path(username)

        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)

        if not isinstance(obj, dict):
            raise ValueError("user record must be a JSON object")

        opaque_record = obj.get("opaque_record")
        peers = obj.get("peers")

        if not isinstance(opaque_record, str):
            raise ValueError("opaque_record must be a base64 string")

        if not isinstance(peers, list) or any(
            not isinstance(peer, str) or not peer for peer in peers
        ):
            raise ValueError("peers must be a list of non-empty strings")

        if len(set(peers)) != len(peers):
            raise ValueError("peers contains duplicates")

        try:
            credential_record = base64.b64decode(
                opaque_record,
                validate=True,
            )
        except (ValueError, binascii.Error) as exc:
            raise ValueError("opaque_record is not valid base64") from exc

        if len(credential_record) != self.opaque_record_len:
            raise ValueError("invalid OPAQUE record size")

        return WGAuthUser(
            username=username,
            credential_record=credential_record,
            peers=tuple(peers),
        )
