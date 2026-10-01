# `src/wg_client/wg_client_API_handler.py`

## Metadata

- Path: `src/wg_client/wg_client_API_handler.py`
- Language: `python`
- Lines: 513
- SHA256: `2b01acb4e6957e4539c5106d8f9720f27a21cb04a15f40d628afa9bbde27362f`
- Imports:
  - `datetime`
  - `http`
  - `http.server`
  - `json`
  - `logging`
  - `src.wg_client.wg_client_errors`
  - `threading`
  - `urllib.parse`

## Source

```python
#!/usr/bin/env python3
import datetime
import http.server
import json
import logging
import threading
from http import HTTPStatus
from urllib.parse import unquote, urlsplit

import src.wg_client.wg_client_errors
from src.wg_client.wg_client_errors import (
    WGMalformedMessageError,
    WGInvalidFieldError,
    WGInvalidEncodingError,
    WGCounterError,
    WGInvalidMACError,
    WGSessionMismatchError,
    WGReplayError,
    WGSessionExpiredError,
)

log = logging.getLogger("wg_manager.api.handler")


MAX_BODY_SIZE = 65536

PEERS_PREFIX = "/v1/peers/"

# Headers used to carry WGSecureSession authentication over HTTPS.
# Not frozen yet as part of the wire protocol: convenient for this
# integration, may still change.
AUTH_SESSION_ID_HEADER = "X-WG-Session-ID"
AUTH_COUNTER_HEADER = "X-WG-Counter"
AUTH_NONCE_HEADER = "X-WG-Nonce"
AUTH_MAC_HEADER = "X-WG-MAC"

# Exceptions that verify_request()/request_auth_headers() can raise for a
# malformed/missing authentication attempt (never reveal a valid session
# state to the caller).
_AUTH_MALFORMED_ERRORS = (
    WGMalformedMessageError,
    WGInvalidFieldError,
    WGInvalidEncodingError,
)

# Exceptions that mean "authentication was attempted but rejected"
# (bad MAC, wrong session, replay, counter out of range/exhausted).
_AUTH_REJECTED_ERRORS = (
    WGCounterError,
    WGInvalidMACError,
    WGSessionMismatchError,
    WGReplayError,
    WGSessionExpiredError,
)


class WGClientHTTPServer(http.server.ThreadingHTTPServer):
    def __init__(
            self,
            server_address,
            handler_class,
            controller,
            listen_path,
            interface,
            lifecycle,
            session=None,
            principal=None,
    ):
        super().__init__(server_address, handler_class)
        self.controller = controller
        self.listen_path = listen_path
        self.interface = interface
        self.lifecycle = lifecycle

        # WGSecureSession used to authenticate requests/responses on this
        # server, or None to run unauthenticated (e.g. in tests that don't
        # care about transport authentication).
        self.session = session
        self.principal = principal

        # ThreadingHTTPServer hands each request to its own thread, but
        # WGSecureSession carries mutable per-session state (the request
        # and response counters). At most one authenticated transaction
        # (verify_request -> controller -> create_response_auth) may be
        # in flight at a time.
        self.session_lock = threading.Lock()


class WGClientAPIHandler(http.server.BaseHTTPRequestHandler):
    # Socket timeout: a client that stops sending cannot hold
    # a handler thread forever.
    timeout = 30

    # Class-level default so that self.request_auth is always readable
    # (e.g. from send_error()) even for methods that error out before
    # ever calling authenticate_request(), such as do_CONNECT/do_PATCH.
    request_auth = None

    def handle_one_request(self):
        # Connections may be persistent (HTTP/1.1 keep-alive), so a
        # single handler instance can serve several requests. Reset the
        # per-request authentication state up front so a stale
        # self.request_auth from a previous request on the same
        # connection never leaks into this one (relevant for do_CONNECT/
        # do_PATCH, which never call authenticate_request() themselves).
        self.request_auth = None
        super().handle_one_request()

    @property
    def controller(self):
        return self.server.controller
    @property
    def lifecycle(self):
        return self.server.lifecycle

    @property
    def session(self):
        return self.server.session

    @property
    def principal(self):
        return self.server.principal

    @property
    def session_lock(self):
        return self.server.session_lock

    def api_path(self):
        """
        Return the request path relative to listen_path, or None
        if the request is outside listen_path.

        The result is still percent-encoded, and does NOT include the
        query string: use this for routing decisions only. For secure
        session authentication use api_target() instead.
        """
        path = urlsplit(self.path).path
        prefix = self.server.listen_path

        if not path.startswith(prefix + "/"):
            return None

        return path[len(prefix) :]

    def api_target(self):
        """
        Return the request target relative to listen_path, including
        the query string if present, or None if the request is outside
        listen_path.

        This is the exact string that must be authenticated: the query
        string can carry application-level meaning, so it has to be
        part of what create_request_auth()/verify_request() sign, even
        though routing (api_path()) ignores it.
        """
        parsed = urlsplit(self.path)
        path = parsed.path
        prefix = self.server.listen_path

        if not path.startswith(prefix + "/"):
            return None

        target = path[len(prefix):]

        if parsed.query:
            target += "?" + parsed.query

        return target

    def peer_key(self, path):
        """Return the decoded public key from /v1/peers/<pk>, or None."""
        if path is None or not path.startswith(PEERS_PREFIX):
            return None

        public_key = unquote(path[len(PEERS_PREFIX) :])

        return public_key or None

    def log_message(self, format, *args):
        log.info("HTTP %s - %s", self.address_string(), format % args)

    # ------------------------------------------------------------------
    # Secure session authentication
    # ------------------------------------------------------------------

    def request_auth_headers(self):
        """
        Extract and lightly parse the X-WG-* authentication headers.

        Raises WGMalformedMessageError if any header is missing, or
        WGInvalidFieldError if X-WG-Counter is not an integer. The
        rest of the field validation (base64, sizes, counter range)
        is WGSecureSession's job, via verify_request().
        """
        session_id = self.headers.get(AUTH_SESSION_ID_HEADER)
        counter = self.headers.get(AUTH_COUNTER_HEADER)
        nonce = self.headers.get(AUTH_NONCE_HEADER)
        mac = self.headers.get(AUTH_MAC_HEADER)

        if session_id is None or counter is None or nonce is None or mac is None:
            raise WGMalformedMessageError("missing secure-session authentication headers")

        try:
            counter = int(counter)
        except ValueError as exc:
            raise WGInvalidFieldError(f"{AUTH_COUNTER_HEADER} must be an integer") from exc

        return {
            "session_id": session_id,
            "counter": counter,
            "nonce": nonce,
            "mac": mac,
        }

    def authenticate_request(self, body):
        """
        Authenticate the current request against self.session, using
        self.command as the HTTP method and api_target() (relative to
        listen_path, including the query string) as the signed path.

        On success, sets self.request_auth to the validated auth dict
        (needed later to sign the response) and returns True.

        On failure, sends the appropriate HTTP error response itself
        (never authenticated: there is no valid request to bind a
        response MAC to) and returns False. The caller must simply
        return without doing anything else.

        If self.session is None (secure session disabled/not wired for
        this server, e.g. in tests), authentication is skipped entirely
        and the request is treated as trusted.
        """
        self.request_auth = None

        target = self.api_target()

        if target is None:
            self.send_error(404)
            return False

        if self.session is None:
            return True

        try:
            auth = self.request_auth_headers()
            self.session.verify_request(auth, self.command, target, body)

        except _AUTH_MALFORMED_ERRORS as exc:
            log.warning("malformed secure-session authentication: %s", exc)
            self.send_error(400, "Bad Request", "invalid secure-session authentication")
            return False

        except _AUTH_REJECTED_ERRORS as exc:
            log.warning("secure-session authentication rejected: %s", exc)
            self.send_error(401, "Unauthorized", "secure-session authentication failed")
            return False

        self.request_auth = auth
        return True

    def _authenticated_headers(self, code, body):
        """
        Build the X-WG-* response headers for `body` sent with `code`,
        signing against self.request_auth (the request this response
        answers). Returns {} if there is no session, or no successfully
        authenticated request to bind to (self.request_auth is None):
        an unauthenticated request never gets an authenticated response,
        authenticated or not (see point 12 of the integration notes).
        """
        if self.session is None or self.request_auth is None:
            return {}

        response_auth = self.session.create_response_auth(
            self.request_auth,
            code,
            body,
        )

        return {
            AUTH_SESSION_ID_HEADER: response_auth["session_id"],
            AUTH_COUNTER_HEADER: str(response_auth["counter"]),
            AUTH_MAC_HEADER: response_auth["mac"],
        }

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def send_error(self, code, message=None, explain=None):
        """JSON style override for send_error, authenticated when possible."""

        try:
            shortmsg, longmsg = self.responses[code]
        except KeyError:
            shortmsg, longmsg = "???", "???"

        if message is None:
            message = shortmsg
        if explain is None:
            explain = longmsg

        self.log_error("code %d, message %s", code, message)

        body = None

        if code >= 200 and code not in (
            HTTPStatus.NO_CONTENT,
            HTTPStatus.RESET_CONTENT,
            HTTPStatus.NOT_MODIFIED,
        ):
            timestamp = (
                datetime.datetime.utcnow()
                .replace(tzinfo=datetime.timezone.utc)
                .isoformat()
            )
            content = {
                "timestamp": timestamp,
                "status": code,
                "error": message,
                "message": explain,
                "path": self.path,
            }
            body = json.dumps(content).encode("utf-8")

        # request_auth may not exist yet if send_error() fires before
        # authenticate_request() ever ran (e.g. TRACE/unsupported method).
        auth_headers = self._authenticated_headers(code, body or b"")

        self.send_response(code, message)

        # Authenticated errors keep the connection alive like any other
        # authenticated response; an unauthenticated error still closes
        # the connection, since the client has nothing to trust it with.
        if not auth_headers:
            self.send_header("Connection", "close")

        for name, value in auth_headers.items():
            self.send_header(name, value)

        if body is not None:
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))

        self.end_headers()

        if self.command != "HEAD" and body:
            self.wfile.write(body)

    def send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")

        auth_headers = self._authenticated_headers(code, body)

        self.send_response(code)

        for name, value in auth_headers.items():
            self.send_header(name, value)

        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        if self.command != "HEAD":
            self.wfile.write(body)

    # ------------------------------------------------------------------
    # Endpoints
    #
    # Every handler follows the same shape:
    #   1. read the raw body exactly as received (if any);
    #   2. acquire session_lock;
    #   3. authenticate_request(raw_body) - bails out (already replied)
    #      on failure;
    #   4. run the controller operation;
    #   5. send_json()/send_error(), which sign the response against
    #      self.request_auth when authentication is in effect.
    #
    # The whole verify -> controller -> respond transaction happens
    # under session_lock, so the response counter always corresponds to
    # the latest accepted request counter even under ThreadingHTTPServer.
    # ------------------------------------------------------------------

    def do_GET(self):
        log.info("Received HTTP GET request: %s", self.path)

        with self.session_lock:
            if not self.authenticate_request(b""):
                return

            if self.api_path() != "/v1/status":
                self.send_error(404)
                return

            try:
                result = self.controller.status()

            except src.wg_client.wg_client_errors.WGControllerError as exc:
                self.send_error(
                    exc.status,
                    "Controller error",
                    exc.message,
                )
                return

            if not isinstance(result, dict) or result.get("interface") != self.server.interface:
                log.error("controller reports an unexpected interface")
                self.send_error(
                    502,
                    "Controller error",
                    "controller interface mismatch",
                )
                return

            self.send_json(200, result)

    def do_POST(self):
        log.info("Received HTTP POST request: %s", self.path)

        with self.session_lock:
            if not self.authenticate_request(b""):
                return

            self.send_json(200, {"status": "ok"})

    def do_DELETE(self):
        log.warning("Received HTTP DELETE request: %s", self.path)

        with self.session_lock:
            if not self.authenticate_request(b""):
                return

            public_key = self.peer_key(self.api_path())

            if public_key is None:
                self.send_error(404)
                return

            try:
                result = self.controller.remove_peer(public_key)

            except src.wg_client.wg_client_errors.WGControllerError as exc:
                self.send_error(
                    exc.status,
                    "Controller error",
                    exc.message,
                )
                return

            self.send_json(200, result)

    def do_CONNECT(self):
        log.warning("Received HTTP CONNECT request: %s", self.path)
        self.send_error(405)

    def do_PATCH(self):
        log.warning("Received HTTP PATCH request: %s", self.path)
        self.send_error(405)

    def do_PUT(self):
        log.warning("Received HTTP PUT request: %s", self.path)

        try:
            length = int(self.headers.get("Content-Length", 0))

            # A negative length would make rfile.read() wait for EOF.
            if not 0 <= length <= MAX_BODY_SIZE:
                raise ValueError("invalid Content-Length")

            raw_body = self.rfile.read(length)

        except ValueError:
            self.send_error(400, "Bad Request", "invalid Content-Length")
            return

        with self.session_lock:
            # The raw body, exactly as received, is what gets
            # authenticated: never re-serialize it before verifying.
            if not self.authenticate_request(raw_body):
                return

            public_key = self.peer_key(self.api_path())

            if public_key is None:
                self.send_error(404)
                return

            try:
                obj = json.loads(raw_body.decode("utf-8"))
                allowed_ip = obj["allowed_ip"]

            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                self.send_error(
                    400,
                    "Bad Request",
                    "Invalid peer request",
                )
                return

            try:
                result = self.controller.add_peer(
                    public_key,
                    allowed_ip,
                )

            except src.wg_client.wg_client_errors.WGControllerError as exc:
                self.send_error(
                    exc.status,
                    "Controller error",
                    exc.message,
                )
                return

            self.send_json(200, result)
```
