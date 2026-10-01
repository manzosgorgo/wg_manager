import json
import logging
import re
import socket
import time

from src.wg_client.wg_client_errors import WGProtocolError
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


class WGClientIPC:

    def __init__(self, sock, lifecycle):
        self.sock = sock
        self.lifecycle = lifecycle


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
            log.debug("IPC control loop stopped")


    def receive_packet(self):
        data = bytearray()

        while True:
            chunk = self.sock.recv(4096)

            if not chunk:
                break

            data.extend(chunk)

            if len(data) > MAX_PACKET_SIZE:
                raise WGProtocolError("packet too large")

            if b"\n" in data:
                break

        if not data:
            raise WGProtocolError("empty packet")

        return bytes(data).split(b"\n", 1)[0]


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

        self.sock.sendall(self._encode_packet(response))

    def _notify_stop(self):
        if self.sock is None:
            return
        log.debug("sending STOP on ipc")
        response = {
            "protocol_version": PROTOCOL_VERSION,
            "type": "STOP",
        }
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
