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

    def __init__(
        self,
        socket_path,
        client_id,
        timeout,
        listen_path,
        lifecycle,
    ):
        self.socket_path = socket_path
        self.client_id = client_id
        self.timeout = timeout
        self.listen_path = listen_path
        self.lifecycle = lifecycle

        self.sock = None
    @property
    def active(self):
        return self.sock is not None

    def control_loop(self):
        log.debug("IPC control loop started")

        try:
            while True:
                packet = self.receive_packet()
                log.debug("received IPC packet: %r", packet)

                try:
                    request = self.parse_packet(packet)
                    log.debug("parsed IPC packet: %r", request)
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

    def receive_packet(self):
        data = bytearray()

        while True:
            chunk = self.sock.recv(4096)

            if not chunk:
                break

            data.extend(chunk)

            if len(data) > MAX_PACKET_SIZE:
                raise WGAuthProtocolError(
                    "packet too large"
                )

            if b"\n" in data:
                break

        if not data:
            raise WGAuthProtocolError(
                "empty packet"
            )

        return bytes(data).split(
            b"\n",
            1,
        )[0]

    def parse_packet(self, packet):
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

        if self.sock is not None:
            raise RuntimeError("IPC already active")

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
            "created_at": int(time.time()),
        }

        self.send_packet(packet)

        response = self.receive_packet()
        response = self.parse_packet(response)

        if response.get("type") != "ACTIVATION_RESULT":
            raise WGAuthProtocolError("invalid activation response")

        if response.get("status") != "OK":
            raise WGAuthProtocolError(
                response.get("error", "activation failed")
            )

        return response
    def deactivate(self):
        if self.sock is None:
            return

        self.send_packet({
            "protocol_version": PROTOCOL_VERSION,
            "type": "STOP",
        })

        self.close()

    def send_packet(self, packet):
        payload = (
                json.dumps(
                    packet,
                    separators=(",", ":")
                ) + "\n"
        ).encode("utf-8")
        self.sock.sendall(payload)

    def close(self):
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
