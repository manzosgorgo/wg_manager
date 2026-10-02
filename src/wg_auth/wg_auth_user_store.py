#!/usr/bin/env python3

import base64
import binascii
import json
import os
import tempfile
import threading
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
        self._lock = threading.RLock()

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


    def _write_user(self, user, *, replace=True):
        path = self._path(user.username)
        record = {
            "opaque_record": base64.b64encode(
                user.credential_record
            ).decode("ascii"),
            "peers": list(user.peers),
        }

        fd, tmp_path = tempfile.mkstemp(
            dir=self.login_dir,
            prefix=f".{user.username}.",
            text=True,
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

            os.chmod(tmp_path, 0o600)

            if replace:
                os.replace(tmp_path, path)
            else:
                os.link(tmp_path, path)
                os.unlink(tmp_path)

        finally:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

    def add_peer(self, username, public_key):
        if not isinstance(public_key, str) or not public_key:
            raise ValueError("public_key must be a non-empty string")

        with self._lock:
            user = self.load(username)

            if public_key in user.peers:
                return user

            updated = WGAuthUser(
                username=user.username,
                credential_record=user.credential_record,
                peers=user.peers + (public_key,),
            )

            self._write_user(updated)
            return updated

    def remove_peer(self, username, public_key):
        if not isinstance(public_key, str) or not public_key:
            raise ValueError("public_key must be a non-empty string")

        with self._lock:
            user = self.load(username)

            if public_key not in user.peers:
                return user

            updated = WGAuthUser(
                username=user.username,
                credential_record=user.credential_record,
                peers=tuple(
                    peer for peer in user.peers
                    if peer != public_key
                ),
            )

            self._write_user(updated)
            return updated


    def create_user(self, username, credential_record):
        if not isinstance(credential_record, bytes):
            raise ValueError("credential_record must be bytes")

        if len(credential_record) != self.opaque_record_len:
            raise ValueError("invalid OPAQUE record size")

        with self._lock:
            user = WGAuthUser(
                username=username,
                credential_record=credential_record,
                peers=(),
            )
            self._path(username)
            self._write_user(user, replace=False)
            return user

    def delete_user(self, username):
        with self._lock:
            user = self.load(username)

            if user.peers:
                raise ValueError(
                    "cannot delete user while owned peers still exist"
                )

            os.unlink(self._path(username))
