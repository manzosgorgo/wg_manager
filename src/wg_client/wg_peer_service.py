#!/usr/bin/env python3

import logging

from src.wg_client.wg_client_errors import (
    WGControllerError,
    WGPeerError,
    WGProtocolError,
)

log = logging.getLogger("wg_manager.peer_service")


class WGPeerService:
    """Authorization and consistency boundary for peer operations."""

    def __init__(self, controller, session, lifecycle, interface):
        if session is None:
            raise RuntimeError("WGPeerService requires a secure session")

        if session.principal is None:
            raise RuntimeError("WGPeerService requires an authenticated principal")

        self.controller = controller
        self.session = session
        self.lifecycle = lifecycle
        self.interface = interface

    @property
    def ipc(self):
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

    def add_peer(self, public_key, allowed_ip):
        current = self._controller_status()

        existing_keys = {
            peer.get("public_key")
            for peer in current.get("peers", [])
            if isinstance(peer, dict)
        }

        if (
            public_key in existing_keys
            and not self.session.can_access_peer(public_key)
        ):
            raise WGPeerError(
                403,
                "peer is not owned by this principal",
            )

        try:
            self.ipc.register_peer(public_key)
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
        except WGProtocolError as exc:
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
