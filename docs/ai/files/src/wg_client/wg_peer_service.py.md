# `src/wg_client/wg_peer_service.py`

## Metadata

- Path: `src/wg_client/wg_peer_service.py`
- Language: `python`
- Lines: 341
- SHA256: `88b929e713faa087b4936fd457a8b5a7dbf98929f13084d77f03eb151bfa3dd4`
- Imports:
  - `ipaddress`
  - `logging`
  - `src.wg_client.wg_client_errors`

## Source

```python
#!/usr/bin/env python3

"""
Authorization and consistency layer between the HTTP API, wg-auth persistence and controller.

User-visible peer operations are authorized against the authenticated principal.
Creation reserves ownership before mutating WireGuard and rolls back on controller
failure; removal mutates the controller first and reports persistence cleanup
failures as consistency errors. Admin methods delegate account/ownership state
to wg-auth over IPC.
"""

import ipaddress
import logging

from src.wg_client.wg_client_errors import (
    WGControllerError,
    WGPeerError,
    WGPeerPersistenceError,
    WGProtocolError,
)

log = logging.getLogger("wg_manager.peer_service")


class WGPeerService:
    """Authorization and consistency boundary for peer operations."""

    def __init__(self, controller, session, lifecycle, interface, endpoint=None):
        """
        Bind controller, authenticated principal, lifecycle, interface and provisioning endpoint.
        """
        if session is None:
            raise RuntimeError("WGPeerService requires a secure session")

        if session.principal is None:
            raise RuntimeError("WGPeerService requires an authenticated principal")

        self.controller = controller
        self.session = session
        self.lifecycle = lifecycle
        self.interface = interface
        self.endpoint = endpoint

    @property
    def ipc(self):
        """
        Return the active persistence IPC channel or raise a 503 peer error.
        """
        ipc = self.lifecycle.ipc
        if ipc is None:
            raise WGPeerError(
                503,
                "peer persistence IPC is unavailable",
            )
        return ipc

    def _controller_status(self):
        try:
            result = self.controller.status()
        except WGControllerError as exc:
            raise WGPeerError(exc.status, exc.message) from exc

        if (
            not isinstance(result, dict)
            or result.get("interface") != self.interface
        ):
            raise WGPeerError(
                502,
                "controller interface mismatch",
            )

        return result

    def status(self):
        """
        Return controller status filtered to peers owned by the principal unless admin.
        """
        result = self._controller_status()

        if self.session.is_admin:
            return result

        filtered = dict(result)
        peers = result.get("peers", [])

        if not isinstance(peers, list):
            raise WGPeerError(
                502,
                "controller returned invalid peer list",
            )

        filtered["peers"] = [
            peer
            for peer in peers
            if isinstance(peer, dict)
            and self.session.can_access_peer(peer.get("public_key"))
        ]

        return filtered

    def provisioning(self):
        """
        Merge controller and persistence state into available/reserved VPN addressing data.
        """
        try:
            controller = self.controller.provisioning()
        except WGControllerError as exc:
            raise WGPeerError(exc.status, exc.message) from exc

        if not isinstance(controller, dict):
            raise WGPeerError(502, "controller returned invalid provisioning state")

        try:
            registry = self.ipc.provisioning_state()
        except WGPeerPersistenceError as exc:
            raise WGPeerError(exc.status, exc.message) from exc
        except WGProtocolError as exc:
            raise WGPeerError(502, "failed to read provisioning state") from exc

        try:
            network = ipaddress.ip_network(
                controller["vpn_network"],
                strict=False,
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise WGPeerError(502, "controller returned invalid VPN network") from exc

        occupied = set(controller.get("used_ips", []))
        if isinstance(registry, dict):
            occupied.update(registry.get("reserved_ips", []))

        server_address = controller.get("server_address")
        if server_address:
            try:
                occupied.add(str(ipaddress.ip_interface(server_address)))
            except ValueError as exc:
                raise WGPeerError(502, "controller returned invalid server address") from exc

        available = []
        prefix = network.max_prefixlen
        for host in network.hosts():
            candidate = f"{host}/{prefix}"
            if candidate not in occupied:
                available.append(candidate)

        result = dict(controller)
        result["endpoint"] = self.endpoint
        result["reserved_ips"] = sorted(occupied)
        result["available_ips"] = available
        return result

    def add_peer(self, public_key, allowed_ip):
        """
        Reserve ownership, add the controller peer, roll back on failure and update session ownership.
        """
        current = self._controller_status()

        existing_keys = {
            peer.get("public_key")
            for peer in current.get("peers", [])
            if isinstance(peer, dict)
        }

        if public_key in existing_keys:
            if not self.session.can_access_peer(public_key):
                raise WGPeerError(
                    403,
                    "peer is not owned by this principal",
                )

            raise WGPeerError(
                409,
                "public key already exists",
            )

        try:
            self.ipc.register_peer(
                public_key,
                allowed_ip,
            )
        except WGPeerPersistenceError as exc:
            raise WGPeerError(
                exc.status,
                exc.message,
            ) from exc
        except WGProtocolError as exc:
            raise WGPeerError(
                502,
                "failed to persist peer ownership",
            ) from exc

        try:
            result = self.controller.add_peer(
                public_key,
                allowed_ip,
            )

        except WGControllerError as exc:
            try:
                self.ipc.unregister_peer(public_key)
            except (WGProtocolError, WGPeerError) as rollback_exc:
                log.exception(
                    "peer creation failed and ownership rollback failed"
                )
                raise WGPeerError(
                    502,
                    "peer creation failed and ownership rollback failed",
                ) from rollback_exc

            raise WGPeerError(
                exc.status,
                exc.message,
            ) from exc

        self.session.register_peer(public_key)
        return result

    def remove_peer(self, public_key):
        """
        Authorize and remove a peer, then clean persisted ownership and session state.
        """
        if not self.session.can_access_peer(public_key):
            raise WGPeerError(
                403,
                "peer is not owned by this principal",
            )

        try:
            result = self.controller.remove_peer(public_key)
        except WGControllerError as exc:
            raise WGPeerError(
                exc.status,
                exc.message,
            ) from exc

        try:
            self.ipc.unregister_peer(public_key)
        except (WGPeerPersistenceError, WGProtocolError) as exc:
            log.error(
                "peer removed but ownership cleanup failed: %s",
                exc,
            )
            raise WGPeerError(
                502,
                "peer was removed but ownership cleanup failed",
            ) from exc

        self.session.unregister_peer(public_key)
        return result


    def admin_status(self):
        """
        Return admin-only combined live runtime and persistent ownership state.
        """
        if not self.session.is_admin:
            raise WGPeerError(403, "admin principal required")

        try:
            ownership = self.ipc.ownership_state()
        except WGPeerPersistenceError as exc:
            raise WGPeerError(exc.status, exc.message) from exc
        except WGProtocolError as exc:
            raise WGPeerError(502, "failed to read ownership state") from exc

        live = self._controller_status()
        live_by_key = {
            peer.get("public_key"): peer
            for peer in live.get("peers", [])
            if isinstance(peer, dict)
            and isinstance(peer.get("public_key"), str)
        }

        rows = []

        for entry in ownership.get("peers", []):
            row = dict(entry)
            live_peer = live_by_key.get(entry.get("public_key"))
            if live_peer is not None:
                row["runtime"] = live_peer
            else:
                row["runtime"] = None
            rows.append(row)

        return {
            "ok": True,
            "users": ownership.get("users", []),
            "peers": rows,
            "ips": ownership.get("ips", {}),
        }

    def reassign_owner(self, public_key, username):
        """
        Admin-only reassignment of a live peer to another persisted user.
        """
        if not self.session.is_admin:
            raise WGPeerError(403, "admin principal required")

        try:
            return self.ipc.reassign_owner(
                public_key,
                username,
            )
        except WGPeerPersistenceError as exc:
            raise WGPeerError(exc.status, exc.message) from exc
        except WGProtocolError as exc:
            raise WGPeerError(502, "failed to update peer ownership") from exc


    def create_user(self, username, password):
        """
        Admin-only account creation through wg-auth persistence IPC.
        """
        if not self.session.is_admin:
            raise WGPeerError(403, "admin principal required")

        try:
            return self.ipc.create_user(username, password)
        except WGPeerPersistenceError as exc:
            raise WGPeerError(exc.status, exc.message) from exc
        except WGProtocolError as exc:
            raise WGPeerError(502, "failed to create account") from exc

    def delete_user(self, username):
        """
        Admin-only account deletion; the currently active admin account cannot delete itself.
        """
        if not self.session.is_admin:
            raise WGPeerError(403, "admin principal required")

        current = self.session.principal.get("username")
        if username == current:
            raise WGPeerError(409, "cannot delete active admin account")

        try:
            return self.ipc.delete_user(username)
        except WGPeerPersistenceError as exc:
            raise WGPeerError(exc.status, exc.message) from exc
        except WGProtocolError as exc:
            raise WGPeerError(502, "failed to delete account") from exc
```
