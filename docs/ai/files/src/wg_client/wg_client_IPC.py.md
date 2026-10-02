# `src/wg_client/wg_client_IPC.py`

## Metadata

- Path: `src/wg_client/wg_client_IPC.py`
- Language: `python`
- Lines: 687
- SHA256: `f81f4f2be98c6343bff48b1479e1f339e4b6ad1fb9086afe1c2b1edb6c152973`
- Imports:
  - `json`
  - `logging`
  - `re`
  - `socket`
  - `src.wg_client.wg_client_errors`
  - `threading`
  - `time`

## Source

```python
import json
import logging
import re
import socket
import threading
import time

from src.wg_client.wg_client_errors import WGProtocolError, WGPeerPersistenceError
log = logging.getLogger("wg_manager.IPC")

MAX_PACKET_SIZE = 65536

PROTOCOL_VERSION = 1

# OPAQUE shared secret size produced by the supported library version.
OPAQUE_SESSION_KEY_SIZE = 64

# Upper bound for the session lifetime requested by auth.
MAX_SESSION_TIMEOUT = 24 * 3600

# Tolerated clock difference between auth and wg_client.
MAX_CLOCK_SKEW = 30

LISTEN_PATH_RE = re.compile(r"(/[A-Za-z0-9_-]+)+")
IPC_RESPONSE_TIMEOUT = 10


class WGClientIPC:

    def __init__(self, sock, lifecycle):
        self.sock = sock
        self.lifecycle = lifecycle

        self._send_lock = threading.Lock()
        self._recv_buffer = bytearray()
        self._pending_lock = threading.Lock()
        self._pending = {}
        self._next_request_id = 1


    def control_loop(self):
        log.debug("IPC control loop started")

        try:
            while True:
                try:
                    packet = self.receive_packet()

                except WGProtocolError as exc:
                    if str(exc) == "empty packet":
                        log.info("IPC connection closed by peer")
                        self.lifecycle.request_shutdown(notify_shutdown=False)
                        return

                    log.error("IPC protocol error: %s", exc)
                    self.lifecycle.request_shutdown()
                    return

                try:
                    request = self.parse_packet(packet)
                except WGProtocolError as exc:
                    log.error("invalid IPC packet: %s", exc)
                    self.lifecycle.request_shutdown()
                    return

                command = request.get("type")

                if command == "STOP":
                    log.info("received STOP command")
                    self.lifecycle.request_shutdown(notify_shutdown=False)
                    return

                if command in ("PEER_RESULT", "OWNERSHIP_RESULT", "ACCOUNT_RESULT", "PROVISIONING_RESULT"):
                    self._complete_pending(request)
                    continue

                log.error("unknown IPC command: %r", command)
                self.lifecycle.request_shutdown()
                return

        except OSError as exc:
            log.error("IPC error: %s", exc)
            self.lifecycle.request_shutdown()

        except Exception:
            log.exception("unexpected error in IPC control loop")
            self.lifecycle.request_shutdown()

        finally:
            self._fail_pending("IPC control loop stopped")
            log.debug("IPC control loop stopped")


    def receive_packet(self):
        while True:
            newline = self._recv_buffer.find(b"\n")

            if newline >= 0:
                if newline > MAX_PACKET_SIZE:
                    raise WGProtocolError("packet too large")

                packet = bytes(self._recv_buffer[:newline])
                del self._recv_buffer[:newline + 1]
                return packet

            if len(self._recv_buffer) > MAX_PACKET_SIZE:
                raise WGProtocolError("packet too large")

            chunk = self.sock.recv(4096)

            if not chunk:
                if not self._recv_buffer:
                    raise WGProtocolError("empty packet")

                packet = bytes(self._recv_buffer)
                self._recv_buffer.clear()
                return packet

            self._recv_buffer.extend(chunk)


    def parse_packet(self,packet):
        try:
            text = packet.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WGProtocolError("packet is not valid UTF-8") from exc

        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            raise WGProtocolError("packet is not valid JSON") from exc

        if not isinstance(obj, dict):
            raise WGProtocolError("packet JSON root must be an object")

        if obj.get("protocol_version") != PROTOCOL_VERSION:
            raise WGProtocolError("unsupported protocol_version")

        return obj


    def _int_field(self,obj, name):
        value = obj.get(name)

        # bool is a subclass of int.
        if type(value) is not int:
            raise WGProtocolError(f"{name} must be an integer")

        return value


    def _hex_field(self,obj, name):
        value = obj.get(name)

        if not isinstance(value, str):
            raise WGProtocolError(f"{name} must be a hex string")

        try:
            return bytes.fromhex(value)
        except ValueError as exc:
            raise WGProtocolError(f"{name} must be a hex string") from exc


    def parse_activation(self,obj, now=None):
        """
        Validate an activation packet.

        Returns a dict with decoded session_id and k_session (bytes),
        client_id, listen_path and expires_at (unix time).

        The OPAQUE session key length belongs to the activation protocol;
        WGSecureSession's configured session_key_size controls only the
        length of keys derived locally with HKDF.
        """
        if now is None:
            now = time.time()

        if obj.get("protocol_version") != PROTOCOL_VERSION:
            raise WGProtocolError("unsupported protocol_version")

        session_id = self._hex_field(obj, "session_id")
        k_session = self._hex_field(obj, "k_session")

        if len(k_session) != OPAQUE_SESSION_KEY_SIZE:
            raise WGProtocolError(
                f"k_session must be {OPAQUE_SESSION_KEY_SIZE} bytes"
            )

        client_id = obj.get("client_id")

        if not isinstance(client_id, str) or not client_id:
            raise WGProtocolError("client_id must be a non-empty string")

        principal = obj.get("principal")
        if not isinstance(principal, dict):
            raise WGProtocolError("principal must be an object")

        username = principal.get("username")
        if not isinstance(username, str) or not username.strip():
            raise WGProtocolError("principal.username must be a non-empty string")

        peers = principal.get("peers")
        if not isinstance(peers, list) or any(
            not isinstance(peer, str) or not peer for peer in peers
        ):
            raise WGProtocolError(
                "principal.peers must be a list of non-empty strings"
            )

        if len(set(peers)) != len(peers):
            raise WGProtocolError("principal.peers contains duplicates")

        principal = {
            "username": username,
            "peers": list(peers),
        }

        listen_path = obj.get("listen_path")

        if not isinstance(listen_path, str) or not LISTEN_PATH_RE.fullmatch(listen_path):
            raise WGProtocolError("invalid listen_path")

        timeout = self._int_field(obj, "timeout")
        created_at = self._int_field(obj, "created_at")

        if not 0 < timeout <= MAX_SESSION_TIMEOUT:
            raise WGProtocolError("timeout out of range")

        if created_at > now + MAX_CLOCK_SKEW:
            raise WGProtocolError("created_at is in the future")

        expires_at = created_at + timeout

        if expires_at <= now:
            raise WGProtocolError("session already expired")

        return {
            "session_id": session_id,
            "k_session": k_session,
            "client_id": client_id,
            "principal": principal,
            "listen_path": listen_path,
            "expires_at": expires_at,
        }


    def _complete_pending(self, response):
        request_id = response.get("request_id")

        if type(request_id) is not int:
            raise WGProtocolError("invalid IPC result request_id")

        with self._pending_lock:
            pending = self._pending.get(request_id)

        if pending is None:
            raise WGProtocolError("unexpected IPC result request_id")

        pending["response"] = response
        pending["event"].set()

    def _fail_pending(self, error):
        with self._pending_lock:
            pending = list(self._pending.values())

        for item in pending:
            item["error"] = error
            item["event"].set()

    def _peer_request(self, command, public_key, allowed_ip=None):
        if command not in ("PEER_REGISTER", "PEER_UNREGISTER"):
            raise WGProtocolError("invalid peer IPC command")

        if not isinstance(public_key, str) or not public_key:
            raise WGProtocolError("public_key must be a non-empty string")

        if command == "PEER_REGISTER":
            if not isinstance(allowed_ip, str) or not allowed_ip:
                raise WGProtocolError(
                    "allowed_ip must be a non-empty string"
                )

        event = threading.Event()

        with self._pending_lock:
            request_id = self._next_request_id
            self._next_request_id += 1
            self._pending[request_id] = {
                "event": event,
                "response": None,
                "error": None,
            }

        packet = {
            "protocol_version": PROTOCOL_VERSION,
            "type": command,
            "request_id": request_id,
            "public_key": public_key,
        }

        if command == "PEER_REGISTER":
            packet["allowed_ip"] = allowed_ip

        try:
            sock = self.sock
            if sock is None:
                raise WGProtocolError("IPC connection is closed")

            try:
                with self._send_lock:
                    sock.sendall(self._encode_packet(packet))
            except OSError as exc:
                raise WGProtocolError(
                    f"IPC peer request failed: {exc}"
                ) from exc

            if not event.wait(IPC_RESPONSE_TIMEOUT):
                raise WGProtocolError("IPC peer request timed out")

            with self._pending_lock:
                pending = self._pending.get(request_id)

            if pending is None:
                raise WGProtocolError("IPC peer request disappeared")

            if pending["error"] is not None:
                raise WGProtocolError(pending["error"])

            response = pending["response"]

            if not isinstance(response, dict):
                raise WGProtocolError("missing PEER_RESULT")

            if response.get("status") != "OK":
                status_code = response.get("status_code", 502)
                if type(status_code) is not int:
                    status_code = 502

                raise WGPeerPersistenceError(
                    status_code,
                    response.get("error", "peer persistence failed"),
                )

            return response

        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def register_peer(self, public_key, allowed_ip):
        return self._peer_request(
            "PEER_REGISTER",
            public_key,
            allowed_ip,
        )

    def unregister_peer(self, public_key):
        return self._peer_request("PEER_UNREGISTER", public_key)

    def _ownership_request(self, command, **fields):
        if command not in ("OWNERSHIP_STATE", "OWNERSHIP_REASSIGN"):
            raise WGProtocolError("invalid ownership IPC command")

        event = threading.Event()

        with self._pending_lock:
            request_id = self._next_request_id
            self._next_request_id += 1
            self._pending[request_id] = {
                "event": event,
                "response": None,
                "error": None,
            }

        packet = {
            "protocol_version": PROTOCOL_VERSION,
            "type": command,
            "request_id": request_id,
            **fields,
        }

        try:
            sock = self.sock
            if sock is None:
                raise WGProtocolError("IPC connection is closed")

            with self._send_lock:
                sock.sendall(self._encode_packet(packet))

            if not event.wait(IPC_RESPONSE_TIMEOUT):
                raise WGProtocolError("ownership IPC request timed out")

            with self._pending_lock:
                pending = self._pending.get(request_id)

            if pending is None:
                raise WGProtocolError("ownership IPC request disappeared")

            if pending["error"] is not None:
                raise WGProtocolError(pending["error"])

            response = pending["response"]

            if not isinstance(response, dict):
                raise WGProtocolError("missing OWNERSHIP_RESULT")

            if response.get("status") != "OK":
                status_code = response.get("status_code", 502)
                if type(status_code) is not int:
                    status_code = 502

                raise WGPeerPersistenceError(
                    status_code,
                    response.get("error", "ownership request failed"),
                )

            return response.get("result")

        except OSError as exc:
            raise WGProtocolError(
                f"ownership IPC request failed: {exc}"
            ) from exc

        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def provisioning_state(self):
        event = threading.Event()

        with self._pending_lock:
            request_id = self._next_request_id
            self._next_request_id += 1
            self._pending[request_id] = {
                "event": event,
                "response": None,
                "error": None,
            }

        packet = {
            "protocol_version": PROTOCOL_VERSION,
            "type": "PROVISIONING_STATE",
            "request_id": request_id,
        }

        try:
            with self._send_lock:
                self.sock.sendall(self._encode_packet(packet))

            if not event.wait(IPC_RESPONSE_TIMEOUT):
                raise WGProtocolError("provisioning IPC request timed out")

            with self._pending_lock:
                pending = self._pending.get(request_id)

            if pending is None:
                raise WGProtocolError("provisioning IPC request disappeared")

            if pending["error"] is not None:
                raise WGProtocolError(pending["error"])

            response = pending["response"]
            if not isinstance(response, dict):
                raise WGProtocolError("missing PROVISIONING_RESULT")

            if response.get("status") != "OK":
                raise WGPeerPersistenceError(
                    response.get("status_code", 502),
                    response.get("error", "provisioning request failed"),
                )

            return response.get("result")

        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def ownership_state(self):
        return self._ownership_request("OWNERSHIP_STATE")

    def reassign_owner(self, public_key, username):
        if not isinstance(public_key, str) or not public_key:
            raise WGProtocolError("public_key must be a non-empty string")
        if not isinstance(username, str) or not username:
            raise WGProtocolError("username must be a non-empty string")

        return self._ownership_request(
            "OWNERSHIP_REASSIGN",
            public_key=public_key,
            username=username,
        )

    def _account_request(self, command, **fields):
        if command not in ("ACCOUNT_CREATE", "ACCOUNT_DELETE"):
            raise WGProtocolError("invalid account IPC command")

        event = threading.Event()

        with self._pending_lock:
            request_id = self._next_request_id
            self._next_request_id += 1
            self._pending[request_id] = {
                "event": event,
                "response": None,
                "error": None,
            }

        packet = {
            "protocol_version": PROTOCOL_VERSION,
            "type": command,
            "request_id": request_id,
            **fields,
        }

        try:
            sock = self.sock
            if sock is None:
                raise WGProtocolError("IPC connection is closed")

            with self._send_lock:
                sock.sendall(self._encode_packet(packet))

            if not event.wait(IPC_RESPONSE_TIMEOUT):
                raise WGProtocolError("account IPC request timed out")

            with self._pending_lock:
                pending = self._pending.get(request_id)

            if pending is None:
                raise WGProtocolError("account IPC request disappeared")

            if pending["error"] is not None:
                raise WGProtocolError(pending["error"])

            response = pending["response"]
            if not isinstance(response, dict):
                raise WGProtocolError("missing ACCOUNT_RESULT")

            if response.get("status") != "OK":
                status_code = response.get("status_code", 502)
                if type(status_code) is not int:
                    status_code = 502
                raise WGPeerPersistenceError(
                    status_code,
                    response.get("error", "account request failed"),
                )

            return response.get("result")

        except OSError as exc:
            raise WGProtocolError(
                f"account IPC request failed: {exc}"
            ) from exc

        finally:
            with self._pending_lock:
                self._pending.pop(request_id, None)

    def create_user(self, username, password):
        return self._account_request(
            "ACCOUNT_CREATE",
            username=username,
            password=password,
        )

    def delete_user(self, username):
        return self._account_request(
            "ACCOUNT_DELETE",
            username=username,
        )

    def reconcile_state(self, peers):
        if not isinstance(peers, list):
            raise WGProtocolError("peer snapshot must be a list")

        packet = {
            "protocol_version": PROTOCOL_VERSION,
            "type": "STATE_SNAPSHOT",
            "peers": peers,
        }

        try:
            with self._send_lock:
                self.sock.sendall(self._encode_packet(packet))

            response = self.parse_packet(
                self.receive_packet()
            )

        except OSError as exc:
            raise WGProtocolError(
                f"state reconciliation IPC failed: {exc}"
            ) from exc

        if response.get("type") != "STATE_RESULT":
            raise WGProtocolError("invalid state reconciliation response")

        if response.get("status") != "OK":
            raise WGProtocolError(
                response.get("error", "state reconciliation failed")
            )

        return response

    def _encode_packet(self, packet):
        payload = (
            json.dumps(packet, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )

        if len(payload) > MAX_PACKET_SIZE:
            raise WGProtocolError("packet too large")

        return payload


    def send_result(self, status, **fields):
        if status not in {"OK", "ERROR"}:
            raise WGProtocolError("invalid activation result status")

        response = {
            "protocol_version": PROTOCOL_VERSION,
            "type": "ACTIVATION_RESULT",
            "status": status,
            **fields,
        }

        with self._send_lock:
            self.sock.sendall(self._encode_packet(response))

    def keepalive(self):
        sock = self.sock
        if sock is None:
            raise WGProtocolError("IPC connection is closed")

        packet = {
            "protocol_version": PROTOCOL_VERSION,
            "type": "KEEPALIVE",
        }

        try:
            with self._send_lock:
                sock.sendall(self._encode_packet(packet))
        except OSError as exc:
            raise WGProtocolError(
                f"IPC keepalive failed: {exc}"
            ) from exc

    def _notify_stop(self):
        if self.sock is None:
            return
        log.debug("sending STOP on ipc")
        response = {
            "protocol_version": PROTOCOL_VERSION,
            "type": "STOP",
        }
        with self._send_lock:
            self.sock.sendall(self._encode_packet(response))
        log.debug("sent STOP on ipc")
    def stop(self, notify_shutdown=True):
        sock = self.sock

        if sock is None:
            return

        try:
            if notify_shutdown:
                try:
                    self._notify_stop()
                except OSError as exc:
                    log.warning(
                        "failed to notify peer during IPC shutdown: %s",
                        exc,
                    )

            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        finally:
            try:
                sock.close()
            except OSError:
                pass

            self.sock = None
```
