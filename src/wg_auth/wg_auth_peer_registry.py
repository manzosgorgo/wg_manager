#!/usr/bin/env python3

import json
import os
import tempfile
import threading


class WGAuthPeerRegistry:
    """Persistent global reservation table for WireGuard keys and IPs."""

    def __init__(self, path):
        self.path = path
        self._lock = threading.RLock()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except FileNotFoundError:
            return {"peers": {}}

        if not isinstance(obj, dict):
            raise ValueError("peer registry must be a JSON object")

        peers = obj.get("peers")
        if not isinstance(peers, dict):
            raise ValueError("peer registry peers must be an object")

        for public_key, entry in peers.items():
            if not isinstance(public_key, str) or not public_key:
                raise ValueError("peer registry contains invalid public key")

            if not isinstance(entry, dict):
                raise ValueError("peer registry entry must be an object")

            username = entry.get("username")
            allowed_ip = entry.get("allowed_ip")
            state = entry.get("ownership_state")
            if state is None:
                state = "consistent" if username is not None else "orphan"
                entry["ownership_state"] = state

            if username is not None and (
                not isinstance(username, str) or not username
            ):
                raise ValueError("peer registry entry has invalid username")

            if not isinstance(allowed_ip, str) or not allowed_ip:
                raise ValueError("peer registry entry has invalid allowed_ip")

            if state not in {"consistent", "orphan"}:
                raise ValueError("peer registry entry has invalid ownership_state")

            if state == "consistent" and username is None:
                raise ValueError("consistent peer registry entry has no owner")

            if state == "orphan" and username is not None:
                raise ValueError("orphan peer registry entry has an owner")

        return obj

    def _write(self, obj):
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=directory,
            prefix=".peer-registry.",
            text=True,
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2, sort_keys=True)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

            os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, self.path)

        finally:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

    def reserve(self, username, public_key, allowed_ip):
        if not isinstance(username, str) or not username:
            raise ValueError("username must be a non-empty string")
        if not isinstance(public_key, str) or not public_key:
            raise ValueError("public_key must be a non-empty string")
        if not isinstance(allowed_ip, str) or not allowed_ip:
            raise ValueError("allowed_ip must be a non-empty string")

        with self._lock:
            obj = self._load()
            peers = obj["peers"]

            existing = peers.get(public_key)
            if existing is not None:
                if (
                    existing.get("username") == username
                    and existing.get("allowed_ip") == allowed_ip
                ):
                    return dict(existing)

                raise ValueError("public key is already reserved")

            for entry in peers.values():
                if entry.get("allowed_ip") == allowed_ip:
                    raise ValueError("allowed IP is already reserved")

            entry = {
                "username": username,
                "allowed_ip": allowed_ip,
                "ownership_state": "consistent",
            }
            peers[public_key] = entry
            self._write(obj)
            return dict(entry)

    def release(self, actor_username, public_key):
        if not isinstance(actor_username, str) or not actor_username:
            raise ValueError("actor username must be a non-empty string")
        if not isinstance(public_key, str) or not public_key:
            raise ValueError("public_key must be a non-empty string")

        with self._lock:
            obj = self._load()
            peers = obj["peers"]
            existing = peers.get(public_key)

            if existing is None:
                return None

            owner = existing["username"]

            if actor_username != "admin" and actor_username != owner:
                raise PermissionError("peer reservation belongs to another user")

            del peers[public_key]
            self._write(obj)

            return dict(existing)

    def get(self, public_key):
        with self._lock:
            entry = self._load()["peers"].get(public_key)
            return None if entry is None else dict(entry)

    def snapshot(self):
        with self._lock:
            return {
                public_key: dict(entry)
                for public_key, entry in self._load()["peers"].items()
            }

    def set_owner(self, public_key, username):
        if not isinstance(username, str) or not username:
            raise ValueError("username must be a non-empty string")

        with self._lock:
            obj = self._load()
            entry = obj["peers"].get(public_key)

            if entry is None:
                raise ValueError("peer is not present in live registry")

            entry["username"] = username
            entry["ownership_state"] = "consistent"
            self._write(obj)

            return dict(entry)

    def reconcile(self, manager_peers, owners):
        """
        Rebuild the registry from the manager's live key/IP state and
        the user store's persisted ownership map.

        manager_peers is a list of {"public_key": str, "allowed_ip": str}.
        owners maps public_key -> username.

        Live peers without a persisted owner are retained as orphan
        reservations so an administrator can claim or reassign them.
        """
        if not isinstance(manager_peers, list):
            raise ValueError("manager peer snapshot must be a list")

        target = {"peers": {}}
        used_ips = set()

        for peer in manager_peers:
            if not isinstance(peer, dict):
                raise ValueError("manager peer snapshot contains invalid entry")

            public_key = peer.get("public_key")
            allowed_ip = peer.get("allowed_ip")

            if not isinstance(public_key, str) or not public_key:
                raise ValueError("manager peer snapshot contains invalid public key")

            if not isinstance(allowed_ip, str) or not allowed_ip:
                raise ValueError("manager peer snapshot contains invalid allowed_ip")

            username = owners.get(public_key)

            if public_key in target["peers"]:
                raise ValueError("manager peer snapshot contains duplicate public key")

            if allowed_ip in used_ips:
                raise ValueError("manager peer snapshot contains duplicate allowed IP")

            used_ips.add(allowed_ip)
            target["peers"][public_key] = {
                "username": username,
                "allowed_ip": allowed_ip,
                "ownership_state": (
                    "consistent"
                    if isinstance(username, str) and username
                    else "orphan"
                ),
            }

        with self._lock:
            self._write(target)

        return target
