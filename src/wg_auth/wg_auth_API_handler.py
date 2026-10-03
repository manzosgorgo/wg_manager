# src/wg_auth/wg_auth_API_handler.py

"""
HTTPS request handler for the public wg-auth endpoints.

POST /auth starts OPAQUE, POST /auth/verify completes it and activates
wg-client, and GET /status exposes coarse session state. Logout is intentionally
performed through the authenticated wg-client session rather than this API.
"""

import json
import logging
from http.server import BaseHTTPRequestHandler

from src.wg_auth.wg_auth_errors import WGAuthSessionError, WGAuthAuthenticationError, WGAuthError, WGAuthProtocolError

log = logging.getLogger("WGAuth.API_Handler")

class WGAuthAPIHandler(BaseHTTPRequestHandler):
    """
    Translate wg-auth HTTP requests into WGAuthAPI operations and JSON responses.
    """
    api = None

    def _send_json(self, status, payload):
        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)
    def _read_json(self):
        length = int(
            self.headers.get("Content-Length", "0")
        )

        body = self.rfile.read(length)

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            raise WGAuthProtocolError(
                "invalid JSON"
            )

        if not isinstance(request, dict):
            raise WGAuthProtocolError(
                "JSON root must be an object"
            )

        return request
    def _handle_auth_start(self):
        try:
            request = self._read_json()

            log.debug(f"recived auth request:{request}")
            username = request["username"]
            pubU = bytes.fromhex(request["pub"])

            response = self.api.start_authentication(
                username,
                pubU,
            )
            log.debug(f"created auth response: {response}")

            self._send_json(
                200,
                {
                    "ok": True,
                    "response": response.hex(),
                },
            )

        except WGAuthAuthenticationError as exc:
            log.exception("authentication failed: %s", exc)
            self._send_json(
                401,
                {
                    "ok": False,
                    "error": "authentication failed",
                },
            )

        except WGAuthSessionError as exc:
            self._send_json(
                409,
                {
                    "ok": False,
                    "error": str(exc),
                },
            )

        except (KeyError, ValueError, WGAuthProtocolError) as exc:
            log.exception("invalid authentication request: %s", exc)
            self._send_json(
                400,
                {
                    "ok": False,
                    "error": "invalid authentication request",
                },
            )

        except WGAuthError as exc:
            log.error("authentication error: %s", exc)

            self._send_json(
                500,
                {
                    "ok": False,
                    "error": exc.message,
                },
            )

        except Exception:
            log.exception("unexpected authentication error")

            self._send_json(
                500,
                {
                    "ok": False,
                    "error": "internal server error",
                },
            )
    def _handle_auth_verify(self):
        try:
            request = self._read_json()

            authU = bytes.fromhex(request["auth"])

            activation = self.api.finish_authentication(
                authU
            )

            self._send_json(
                200,
                {
                    "ok": True,
                    "authenticated": True,
                    "session_id": self.api.session.session_id,
                    "k_session": self.api.session.k_session,
                    "activation": activation,
                },
            )

        except WGAuthAuthenticationError:
            self._send_json(
                401,
                {
                    "ok": False,
                    "error": "authentication failed",
                },
            )

        except WGAuthSessionError as exc:
            self._send_json(
                409,
                {
                    "ok": False,
                    "error": str(exc),
                },
            )

        except (KeyError, ValueError, WGAuthProtocolError):
            self._send_json(
                400,
                {
                    "ok": False,
                    "error": "invalid authentication request",
                },
            )

        except WGAuthError as exc:
            log.error("authentication error: %s", exc)

            self._send_json(
                500,
                {
                    "ok": False,
                    "error": exc.message,
                },
            )

        except Exception:
            log.exception("unexpected authentication error")

            self._send_json(
                500,
                {
                    "ok": False,
                    "error": "internal server error",
                },
            )

    def do_POST(self):
        """
        Dispatch POST /auth and POST /auth/verify; return JSON protocol errors otherwise.
        """
        if self.path == "/auth":
            self._handle_auth_start()
            return

        if self.path == "/auth/verify":
            self._handle_auth_verify()
            return

        self._send_json(
            404,
            {"ok": False, "error": "not found"},
        )

    def do_DELETE(self):
        """
        Reject direct auth logout because logout requires the authenticated client session.
        """
        if self.path != "/auth":
            self._send_json(
                404,
                {
                    "ok": False,
                    "error": "not found",
                },
            )
            return

        self._send_json(
            405,
            {
                "ok": False,
                "error": "logout requires authenticated wg-client session",
            },
        )

    def do_GET(self):
        """
        Return session status for /status and 404 for other paths.
        """
        if self.path != "/status":
            self._send_json(
                404,
                {"ok": False, "error": "not found"},
            )
            return

        status = self.api.get_session_status()

        self._send_json(
            200,
            {
                "ok": True,
                **status,
            },
        )