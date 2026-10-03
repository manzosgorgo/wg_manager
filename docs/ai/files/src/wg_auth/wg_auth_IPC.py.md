# `src/wg_auth/wg_auth_IPC.py`

## Metadata

- Path: `src/wg_auth/wg_auth_IPC.py`
- Language: `python`
- Lines: 633
- SHA256: `1523539b1109f98fbdb02e7bd8382cd49a1447ffb85bac079cd3b59dded4bda9`
- Imports:
  - `json`
  - `logging`
  - `socket`
  - `src.wg_auth.wg_auth_errors`
  - `time`

## Source

```python
"""
Persistent newline-delimited JSON control channel from wg-auth to wg-client.

The channel carries activation, live-state reconciliation, keepalives, peer
persistence, provisioning state, ownership administration, account operations
and STOP. Protocol violations cause the authenticated session to shut down.
"""

import json
import logging
import socket
import time

from src.wg_auth.wg_auth_errors import WGAuthProtocolError

log = logging.getLogger("wg_manager.auth.IPC")
logging.basicConfig(level=logging.DEBUG)

MAX_PACKET_SIZE = 65536
PROTOCOL_VERSION = 1


class WGAuthIPC:
    """
    Own the auth side of the persistent Unix-domain control connection to wg-client.
    """

    def __init__(
        self,
        socket_path,
        client_id,
        timeout,
        listen_path,
        lifecycle,
        principal=None,
        peer_register=None,
        peer_unregister=None,
        state_reconcile=None,
        provisioning_state=None,
        ownership_state=None,
        ownership_reassign=None,
        account_create=None,
        account_delete=None,
    ):
        """
        Configure activation metadata, lifecycle hooks and persistence/admin callbacks.
        """
        self.socket_path = socket_path
        self.client_id = client_id
        self.timeout = timeout
        self.listen_path = listen_path
        self.lifecycle = lifecycle
        self.principal = principal
        self.peer_register = peer_register
        self.peer_unregister = peer_unregister
        self.state_reconcile = state_reconcile
        self.provisioning_state = provisioning_state
        self.ownership_state = ownership_state
        self.ownership_reassign = ownership_reassign
        self.account_create = account_create
        self.account_delete = account_delete

        self.sock = None
        self._recv_buffer = bytearray()
    @property
    def active(self):
        """
        Return True while the Unix control socket is connected.
        """
        return self.sock is not None

    def control_loop(self):
        """
        Process post-activation control messages until STOP, EOF or a protocol failure.
        """
        log.debug("IPC control loop started")

        try:
            while True:
                packet = self.receive_packet()

                try:
                    request = self.parse_packet(packet)
                    log.debug(
                        "received IPC command: %r",
                        request.get("type"),
                    )
                except WGAuthProtocolError as exc:
                    log.error(
                        "invalid IPC packet: %s",
                        exc,
                    )
                    self.lifecycle.request_session_shutdown()
                    return

                command = request.get("type")

                if command == "STOP":
                    log.info(
                        "received STOP from wg-client"
                    )
                    self.lifecycle.request_session_shutdown(notify_client=False)
                    return

                if command == "KEEPALIVE":
                    self.lifecycle.touch_session()
                    continue

                if command in ("PEER_REGISTER", "PEER_UNREGISTER"):
                    self._handle_peer_request(request)
                    continue

                if command == "PROVISIONING_STATE":
                    self._handle_provisioning_request(request)
                    continue

                if command in ("OWNERSHIP_STATE", "OWNERSHIP_REASSIGN"):
                    self._handle_ownership_request(request)
                    continue

                if command in ("ACCOUNT_CREATE", "ACCOUNT_DELETE"):
                    self._handle_account_request(request)
                    continue

                log.error(
                    "unknown IPC command: %r",
                    command,
                )

                self.lifecycle.request_session_shutdown()
                return

        except WGAuthProtocolError as exc:
            if str(exc) == "empty packet":
                log.info(
                    "IPC connection closed by wg-client"
                )
                self.lifecycle.request_session_shutdown(notify_client=False)
            else:
                log.error(
                    "IPC protocol error: %s",
                    exc,
                )
                self.lifecycle.request_session_shutdown()

        except OSError as exc:
            log.error(
                "IPC error: %s",
                exc,
            )
            self.lifecycle.request_session_shutdown()

        except Exception:
            log.exception(
                "unexpected error in IPC control loop"
            )
            self.lifecycle.request_shutdown()

        finally:
            log.debug("IPC control loop stopped")

    def _handle_peer_request(self, request):
        request_id = request.get("request_id")
        public_key = request.get("public_key")
        allowed_ip = request.get("allowed_ip")

        if type(request_id) is not int or request_id < 1:
            raise WGAuthProtocolError("invalid request_id")

        if not isinstance(public_key, str) or not public_key:
            raise WGAuthProtocolError("invalid public_key")

        username = None
        if isinstance(self.principal, dict):
            username = self.principal.get("username")

        if not isinstance(username, str) or not username:
            raise WGAuthProtocolError("IPC principal is missing")

        try:
            if request["type"] == "PEER_REGISTER":
                if not isinstance(allowed_ip, str) or not allowed_ip:
                    raise WGAuthProtocolError("invalid allowed_ip")
                if self.peer_register is None:
                    raise RuntimeError("peer register callback is unavailable")
                self.peer_register(username, public_key, allowed_ip)
            else:
                if self.peer_unregister is None:
                    raise RuntimeError("peer unregister callback is unavailable")
                self.peer_unregister(username, public_key)

        except PermissionError as exc:
            log.warning("peer persistence request forbidden: %s", exc)
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "PEER_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 403,
                "error": str(exc),
            })
            return

        except ValueError as exc:
            log.warning("peer persistence request rejected: %s", exc)
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "PEER_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 409,
                "error": str(exc),
            })
            return

        except Exception as exc:
            log.exception("peer persistence request failed")
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "PEER_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 500,
                "error": str(exc),
            })
            return

        self.send_packet({
            "protocol_version": PROTOCOL_VERSION,
            "type": "PEER_RESULT",
            "request_id": request_id,
            "status": "OK",
        })

    def _handle_provisioning_request(self, request):
        request_id = request.get("request_id")

        if type(request_id) is not int or request_id < 1:
            raise WGAuthProtocolError("invalid request_id")

        try:
            if self.provisioning_state is None:
                raise RuntimeError("provisioning state callback is unavailable")
            result = self.provisioning_state()
        except Exception as exc:
            log.exception("provisioning request failed")
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "PROVISIONING_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 500,
                "error": str(exc),
            })
            return

        self.send_packet({
            "protocol_version": PROTOCOL_VERSION,
            "type": "PROVISIONING_RESULT",
            "request_id": request_id,
            "status": "OK",
            "result": result,
        })

    def _handle_ownership_request(self, request):
        request_id = request.get("request_id")

        if type(request_id) is not int or request_id < 1:
            raise WGAuthProtocolError("invalid request_id")

        username = None
        if isinstance(self.principal, dict):
            username = self.principal.get("username")

        if username != "admin":
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "OWNERSHIP_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 403,
                "error": "admin principal required",
            })
            return

        try:
            if request["type"] == "OWNERSHIP_STATE":
                if self.ownership_state is None:
                    raise RuntimeError("ownership state callback is unavailable")
                result = self.ownership_state()

            else:
                public_key = request.get("public_key")
                target_username = request.get("username")

                if not isinstance(public_key, str) or not public_key:
                    raise WGAuthProtocolError("invalid public_key")
                if not isinstance(target_username, str) or not target_username:
                    raise WGAuthProtocolError("invalid username")
                if self.ownership_reassign is None:
                    raise RuntimeError(
                        "ownership reassign callback is unavailable"
                    )

                result = self.ownership_reassign(
                    public_key,
                    target_username,
                )

        except FileNotFoundError as exc:
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "OWNERSHIP_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 404,
                "error": str(exc),
            })
            return

        except ValueError as exc:
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "OWNERSHIP_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 409,
                "error": str(exc),
            })
            return

        except Exception as exc:
            log.exception("ownership request failed")
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "OWNERSHIP_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 500,
                "error": str(exc),
            })
            return

        self.send_packet({
            "protocol_version": PROTOCOL_VERSION,
            "type": "OWNERSHIP_RESULT",
            "request_id": request_id,
            "status": "OK",
            "result": result,
        })

    def _handle_account_request(self, request):
        request_id = request.get("request_id")

        if type(request_id) is not int or request_id < 1:
            raise WGAuthProtocolError("invalid request_id")

        principal_username = None
        if isinstance(self.principal, dict):
            principal_username = self.principal.get("username")

        if principal_username != "admin":
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "ACCOUNT_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 403,
                "error": "admin principal required",
            })
            return

        username = request.get("username")
        if not isinstance(username, str) or not username:
            raise WGAuthProtocolError("invalid username")

        try:
            if request["type"] == "ACCOUNT_CREATE":
                password = request.get("password")
                if not isinstance(password, str) or not password:
                    raise WGAuthProtocolError("invalid password")
                if self.account_create is None:
                    raise RuntimeError("account create callback is unavailable")
                result = self.account_create(
                    username,
                    password,
                )
            else:
                if self.account_delete is None:
                    raise RuntimeError("account delete callback is unavailable")
                result = self.account_delete(username)

        except FileExistsError as exc:
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "ACCOUNT_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 409,
                "error": str(exc),
            })
            return

        except FileNotFoundError as exc:
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "ACCOUNT_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 404,
                "error": str(exc),
            })
            return

        except ValueError as exc:
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "ACCOUNT_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 409,
                "error": str(exc),
            })
            return

        except Exception as exc:
            log.exception("account request failed")
            self.send_packet({
                "protocol_version": PROTOCOL_VERSION,
                "type": "ACCOUNT_RESULT",
                "request_id": request_id,
                "status": "ERROR",
                "status_code": 500,
                "error": str(exc),
            })
            return

        self.send_packet({
            "protocol_version": PROTOCOL_VERSION,
            "type": "ACCOUNT_RESULT",
            "request_id": request_id,
            "status": "OK",
            "result": result,
        })

    def receive_packet(self):
        """
        Read one bounded newline-delimited packet from the control socket.
        """
        while True:
            newline = self._recv_buffer.find(b"\n")

            if newline >= 0:
                if newline > MAX_PACKET_SIZE:
                    raise WGAuthProtocolError(
                        "packet too large"
                    )

                packet = bytes(
                    self._recv_buffer[:newline]
                )
                del self._recv_buffer[:newline + 1]
                return packet

            if len(self._recv_buffer) > MAX_PACKET_SIZE:
                raise WGAuthProtocolError(
                    "packet too large"
                )

            chunk = self.sock.recv(4096)

            if not chunk:
                if not self._recv_buffer:
                    raise WGAuthProtocolError(
                        "empty packet"
                    )

                packet = bytes(self._recv_buffer)
                self._recv_buffer.clear()
                return packet

            self._recv_buffer.extend(chunk)

    def parse_packet(self, packet):
        """
        Decode UTF-8 JSON and enforce the IPC protocol version.
        """
        try:
            text = packet.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WGAuthProtocolError(
                "packet is not valid UTF-8"
            ) from exc

        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            raise WGAuthProtocolError(
                "packet is not valid JSON"
            ) from exc

        if not isinstance(obj, dict):
            raise WGAuthProtocolError(
                "packet JSON root must be an object"
            )

        if obj.get("protocol_version") != PROTOCOL_VERSION:
            raise WGAuthProtocolError(
                "unsupported protocol_version"
            )

        return obj

    def activate(self, session_id, k_session):
        """
        Connect, send activation, reconcile live peer state and wait for ACTIVATION_RESULT.
        """

        if self.sock is not None:
            raise RuntimeError("IPC already active")

        self._recv_buffer.clear()

        self.sock = socket.socket(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        )

        self.sock.connect(self.socket_path)

        packet = {
            "protocol_version": PROTOCOL_VERSION,
            "session_id": session_id,
            "k_session": k_session,
            "client_id": self.client_id,
            "timeout": self.timeout,
            "listen_path": self.listen_path,
            "principal": self.principal,
            "created_at": int(time.time()),
        }

        self.send_packet(packet)

        while True:
            response = self.receive_packet()
            response = self.parse_packet(response)

            if response.get("type") == "STATE_SNAPSHOT":
                peers = response.get("peers")

                try:
                    if self.state_reconcile is None:
                        raise RuntimeError(
                            "state reconciliation callback is unavailable"
                        )

                    self.state_reconcile(peers)

                except Exception as exc:
                    log.exception("peer state reconciliation failed")
                    self.send_packet({
                        "protocol_version": PROTOCOL_VERSION,
                        "type": "STATE_RESULT",
                        "status": "ERROR",
                        "error": str(exc),
                    })
                    continue

                self.send_packet({
                    "protocol_version": PROTOCOL_VERSION,
                    "type": "STATE_RESULT",
                    "status": "OK",
                })
                continue

            if response.get("type") != "ACTIVATION_RESULT":
                raise WGAuthProtocolError("invalid activation response")

            if response.get("status") != "OK":
                raise WGAuthProtocolError(
                    response.get("error", "activation failed")
                )

            return response
    def deactivate(self):
        """
        Send STOP to the client and close the control channel.
        """
        if self.sock is None:
            return

        self.send_packet({
            "protocol_version": PROTOCOL_VERSION,
            "type": "STOP",
        })

        self.close()

    def _encode_packet(self, packet):
        payload = (
            json.dumps(packet, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )

        if len(payload) > MAX_PACKET_SIZE:
            raise WGAuthProtocolError(
                "packet too large"
            )

        return payload

    def send_packet(self, packet):
        """
        Encode and send one IPC packet on the active socket.
        """
        self.sock.sendall(self._encode_packet(packet))

    def close(self):
        """
        Idempotently shut down and release the Unix control socket.
        """
        if self.sock is None:
            return

        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.sock.close()
        finally:
            self.sock = None
```
