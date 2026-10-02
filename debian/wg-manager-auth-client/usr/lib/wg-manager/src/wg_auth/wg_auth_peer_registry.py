#!/usr/bin/env python3

import json
import os
import tempfile
import threading


class WGAuthPeerRegistry:
    """Persistent global reservation table for WireGuard keys and IPs."""

    def __init__(self, path, ip_path=None):
        self.path = path
        self.ip_path = (
            ip_path
            if ip_path is not None
            else os.path.join(
                os.path.dirname(path) or ".",
                ".ip_registry.json",
            )
        )
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
        self._write_path(
            self.path,
            obj,
            ".peer-registry.",
        )

    def _load_ips(self):
        try:
            with open(self.ip_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except FileNotFoundError:
            return {"ips": {}}

        if not isinstance(obj, dict):
            raise ValueError("IP registry must be a JSON object")

        ips = obj.get("ips")
        if not isinstance(ips, dict):
            raise ValueError("IP registry ips must be an object")

        for allowed_ip, entry in ips.items():
            if not isinstance(allowed_ip, str) or not allowed_ip:
                raise ValueError("IP registry contains invalid allowed_ip")

            if not isinstance(entry, dict):
                raise ValueError("IP registry entry must be an object")

            public_key = entry.get("public_key")
            username = entry.get("username")
            state = entry.get("ownership_state")

            if not isinstance(public_key, str) or not public_key:
                raise ValueError("IP registry entry has invalid public_key")

            if username is not None and (
                not isinstance(username, str) or not username
            ):
                raise ValueError("IP registry entry has invalid username")

            if state is None:
                state = "consistent" if username is not None else "orphan"
                entry["ownership_state"] = state

            if state not in {"consistent", "orphan"}:
                raise ValueError("IP registry entry has invalid ownership_state")

        return obj

    def _write_path(self, path, obj, prefix):
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=directory,
            prefix=prefix,
            text=True,
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2, sort_keys=True)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

            os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, path)

        finally:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

    def _write_registries(self, peers_obj, ips_obj):
        self._write_path(
            self.path,
            peers_obj,
            ".peer-registry.",
        )
        self._write_path(
            self.ip_path,
            ips_obj,
            ".ip-registry.",
        )

    def reserve(self, username, public_key, allowed_ip):
        if not isinstance(username, str) or not username:
            raise ValueError("username must be a non-empty string")
        if not isinstance(public_key, str) or not public_key:
            raise ValueError("public_key must be a non-empty string")
        if not isinstance(allowed_ip, str) or not allowed_ip:
            raise ValueError("allowed_ip must be a non-empty string")

        with self._lock:
            obj = self._load()
            ip_obj = self._load_ips()
            peers = obj["peers"]
            ips = ip_obj["ips"]

            existing = peers.get(public_key)
            if existing is not None:
                if (
                    existing.get("username") == username
                    and existing.get("allowed_ip") == allowed_ip
                ):
                    return dict(existing)

                raise ValueError("public key is already reserved")

            if allowed_ip in ips:
                raise ValueError("allowed IP is already reserved")

            entry = {
                "username": username,
                "allowed_ip": allowed_ip,
                "ownership_state": "consistent",
            }
            peers[public_key] = entry
            ips[allowed_ip] = {
                "public_key": public_key,
                "username": username,
                "ownership_state": "consistent",
            }
            self._write_registries(obj, ip_obj)
            return dict(entry)

    def release(self, actor_username, public_key):
        if not isinstance(actor_username, str) or not actor_username:
            raise ValueError("actor username must be a non-empty string")
        if not isinstance(public_key, str) or not public_key:
            raise ValueError("public_key must be a non-empty string")

        with self._lock:
            obj = self._load()
            ip_obj = self._load_ips()
            peers = obj["peers"]
            ips = ip_obj["ips"]
            existing = peers.get(public_key)

            if existing is None:
                return None

            owner = existing["username"]

            if actor_username != "admin" and actor_username != owner:
                raise PermissionError("peer reservation belongs to another user")

            del peers[public_key]
            ips.pop(existing["allowed_ip"], None)
            self._write_registries(obj, ip_obj)

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

    def snapshot_ips(self):
        with self._lock:
            return {
                allowed_ip: dict(entry)
                for allowed_ip, entry in self._load_ips()["ips"].items()
            }

    def set_owner(self, public_key, username):
        if not isinstance(username, str) or not username:
            raise ValueError("username must be a non-empty string")

        with self._lock:
            obj = self._load()
            ip_obj = self._load_ips()
            entry = obj["peers"].get(public_key)

            if entry is None:
                raise ValueError("peer is not present in live registry")

            entry["username"] = username
            entry["ownership_state"] = "consistent"

            ip_entry = ip_obj["ips"].get(entry["allowed_ip"])
            if ip_entry is None:
                raise ValueError("IP registry is missing peer reservation")

            ip_entry["username"] = username
            ip_entry["ownership_state"] = "consistent"
            self._write_registries(obj, ip_obj)

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
        ip_target = {"ips": {}}
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
            state = (
                "consistent"
                if isinstance(username, str) and username
                else "orphan"
            )

            target["peers"][public_key] = {
                "username": username,
                "allowed_ip": allowed_ip,
                "ownership_state": state,
            }
            ip_target["ips"][allowed_ip] = {
                "public_key": public_key,
                "username": username,
                "ownership_state": state,
            }

        with self._lock:
            self._write_registries(
                target,
                ip_target,
            )

        return target
