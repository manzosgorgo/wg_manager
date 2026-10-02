# `src/wg_auth/wg_auth_ownership_service.py`

## Metadata

- Path: `src/wg_auth/wg_auth_ownership_service.py`
- Language: `python`
- Lines: 68
- SHA256: `11f0f0980ac8fe46b1941e89f9000e1f4654ead0aa637873757acc4f4eecf475`

## Source

```python
#!/usr/bin/env python3

class WGAuthOwnershipService:
    """Administrative ownership operations shared by IPC and CLI."""

    def __init__(self, user_store, peer_registry):
        self.user_store = user_store
        self.peer_registry = peer_registry

    def admin_state(self):
        owners = self.user_store.peer_owners()
        registry = self.peer_registry.snapshot()
        peers = []

        for public_key, entry in registry.items():
            owner = entry.get("username")
            peers.append({
                "public_key": public_key,
                "allowed_ip": entry.get("allowed_ip"),
                "owner": owner,
                "ownership_state": "consistent" if owner else "orphan",
            })

        live_keys = set(registry)
        for public_key, owner in owners.items():
            if public_key not in live_keys:
                peers.append({
                    "public_key": public_key,
                    "allowed_ip": None,
                    "owner": owner,
                    "ownership_state": "stale",
                })

        return {
            "users": [u.username for u in self.user_store.list_users()],
            "peers": peers,
            "ips": self.peer_registry.snapshot_ips(),
        }

    def reassign(self, public_key, target_username):
        self.user_store.load(target_username)
        reservation = self.peer_registry.get(public_key)
        if reservation is None:
            raise ValueError("peer is not present in live registry")

        owners = self.user_store.peer_owners()
        previous_owner = owners.get(public_key)

        if previous_owner == target_username:
            self.peer_registry.set_owner(public_key, target_username)
            return {"public_key": public_key, "owner": target_username}

        if previous_owner is not None:
            self.user_store.remove_peer(previous_owner, public_key)

        try:
            self.user_store.add_peer(target_username, public_key)
            self.peer_registry.set_owner(public_key, target_username)
        except Exception:
            try:
                self.user_store.remove_peer(target_username, public_key)
                if previous_owner is not None:
                    self.user_store.add_peer(previous_owner, public_key)
            except Exception:
                pass
            raise

        return {"public_key": public_key, "owner": target_username}
```
