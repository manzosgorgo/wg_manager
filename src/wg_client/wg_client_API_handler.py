#!/usr/bin/env python3
"""
Authenticated HTTP routing for the per-session wg-client API.

Every application request is scoped below listen_path and authenticated with
WGSecureSession headers. The handler canonicalizes proxy-normalized dynamic
paths before MAC verification and serializes authenticated request/response
transactions to keep counter state coherent.
"""

import datetime
import http.server
import json
import logging
import threading
from http import HTTPStatus
from urllib.parse import quote, unquote, urlsplit

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
    WGPeerError,
)

log = logging.getLogger("wg_manager.api.handler")


MAX_BODY_SIZE = 65536

PEERS_PREFIX = "/v1/peers/"
ADMIN_PEERS_PATH = "/v1/admin/peers"
ADMIN_PEERS_PREFIX = "/v1/admin/peers/"
ADMIN_USERS_PATH = "/v1/admin/users"
ADMIN_USERS_PREFIX = "/v1/admin/users/"
SESSION_PATH = "/v1/session"
HEARTBEAT_PATH = "/v1/heartbeat"
PROVISIONING_PATH = "/v1/provisioning"

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
    """
    Threading HTTP server carrying peer-service, lifecycle and secure-session state.
    """
    def __init__(
            self,
            server_address,
            handler_class,
            peer_service,
            listen_path,
            session,
            lifecycle,
    ):
        """
        Attach per-session services and the transaction lock to the HTTP server.
        """
        super().__init__(server_address, handler_class)
        self.peer_service = peer_service
        self.listen_path = listen_path
        self.lifecycle = lifecycle

        if session is None:
            raise RuntimeError("WGClientHTTPServer requires a secure session")

        self.session = session

        # ThreadingHTTPServer hands each request to its own thread, but
        # WGSecureSession carries mutable per-session state (the request
        # and response counters). At most one authenticated transaction
        # (verify_request -> controller -> create_response_auth) may be
        # in flight at a time.
        self.session_lock = threading.Lock()


class WGClientAPIHandler(http.server.BaseHTTPRequestHandler):
    """
    Route authenticated session, peer, provisioning and admin HTTP operations.
    """
    # Socket timeout: a client that stops sending cannot hold
    # a handler thread forever.
    timeout = 30

    # Class-level default so that self.request_auth is always readable
    # (e.g. from send_error()) even for methods that error out before
    # ever calling authenticate_request(), such as do_CONNECT/do_PATCH.
    request_auth = None

    def handle_one_request(self):
        """
        Reset per-request auth state before processing a possibly persistent HTTP connection.
        """
        # Connections may be persistent (HTTP/1.1 keep-alive), so a
        # single handler instance can serve several requests. Reset the
        # per-request authentication state up front so a stale
        # self.request_auth from a previous request on the same
        # connection never leaks into this one (relevant for do_CONNECT/
        # do_PATCH, which never call authenticate_request() themselves).
        self.request_auth = None
        super().handle_one_request()

    @property
    def peer_service(self):
        """
        Return the server peer service, enforcing the construction invariant.
        """
        service = self.server.peer_service
        if service is None:
            raise RuntimeError("peer service invariant violated")
        return service

    @property
    def session(self):
        """
        Return the server secure session, enforcing the construction invariant.
        """
        session = self.server.session
        if session is None:
            raise RuntimeError("secure session invariant violated")
        return session

    @property
    def session_lock(self):
        """
        Return the lock serializing authenticated application transactions.
        """
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

    @staticmethod
    def _decode_peer_component(value):
        """
        Decode a peer path component as transported through Apache.

        Apache may require an encoded slash to be double-escaped
        (%2F -> %252F) before proxying the request. Peer public keys are
        standard base64 and cannot contain a literal '%' character, so
        decoding twice is unambiguous for this field while still working
        for directly encoded requests.
        """
        return unquote(unquote(value))

    def api_target(self):
        """
        Return the canonical request target authenticated by
        WGSecureSession.

        Reverse proxies are allowed to normalize percent-encoding in the
        request path (for example "%3D" -> "="). Dynamic path components
        are therefore decoded and re-encoded here before MAC verification,
        so direct clients and proxied browser requests authenticate the
        same logical target.
        """
        parsed = urlsplit(self.path)
        path = parsed.path
        prefix = self.server.listen_path

        if not path.startswith(prefix + "/"):
            return None

        target = path[len(prefix):]

        if target.startswith(PEERS_PREFIX):
            public_key = self._decode_peer_component(
                target[len(PEERS_PREFIX):]
            )
            target = PEERS_PREFIX + quote(public_key, safe="")

        elif (
            target.startswith(ADMIN_PEERS_PREFIX)
            and target.endswith("/owner")
        ):
            encoded = target[
                len(ADMIN_PEERS_PREFIX):-len("/owner")
            ]
            public_key = self._decode_peer_component(encoded)
            target = (
                ADMIN_PEERS_PREFIX
                + quote(public_key, safe="")
                + "/owner"
            )

        elif target.startswith(ADMIN_USERS_PREFIX):
            username = unquote(target[len(ADMIN_USERS_PREFIX):])
            target = ADMIN_USERS_PREFIX + quote(username, safe="")

        if parsed.query:
            target += "?" + parsed.query

        return target

    def peer_key(self, path):
        """Return the decoded public key from /v1/peers/<pk>, or None."""
        if path is None or not path.startswith(PEERS_PREFIX):
            return None

        public_key = self._decode_peer_component(
            path[len(PEERS_PREFIX) :]
        )

        return public_key or None

    def admin_owner_key(self, path):
        """
        Decode the public key from an admin ownership path, or return None.
        """
        if (
            path is None
            or not path.startswith(ADMIN_PEERS_PREFIX)
            or not path.endswith("/owner")
        ):
            return None

        encoded = path[
            len(ADMIN_PEERS_PREFIX):-len("/owner")
        ]

        public_key = self._decode_peer_component(encoded)
        return public_key or None

    def log_message(self, format, *args):
        """
        Route BaseHTTPRequestHandler access messages through the project logger.
        """
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

        The server cannot exist without a secure session.
        """
        self.request_auth = None

        target = self.api_target()

        if target is None:
            self.send_error(404)
            return False

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

        # Only a successfully authenticated browser request proves that
        # the holder of K_session is still attached to this session.
        self.server.lifecycle.notify_activity()

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
        if self.request_auth is None:
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
        """
        Send a JSON response and attach secure-session response authentication when available.
        """
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
        """
        Serve heartbeat, status, provisioning and admin-state GET endpoints.
        """
        log.info("Received HTTP GET request: %s", self.path)

        path = self.api_path()

        # Heartbeat is intentionally independent from the application
        # transaction lock. WGSecureSession protects its own counters,
        # replay window and MAC state internally, and authenticate_request()
        # already refreshes the auth-side idle timer.
        if path == HEARTBEAT_PATH:
            if not self.authenticate_request(b""):
                return

            self.send_json(200, {"ok": True})
            return

        with self.session_lock:
            if not self.authenticate_request(b""):
                return

            try:
                if path == "/v1/status":
                    result = self.peer_service.status()
                elif path == PROVISIONING_PATH:
                    result = self.peer_service.provisioning()
                elif path == ADMIN_PEERS_PATH:
                    result = self.peer_service.admin_status()
                else:
                    self.send_error(404)
                    return

            except WGPeerError as exc:
                self.send_error(
                    exc.status,
                    "Peer service error",
                    exc.message,
                )
                return

            self.send_json(200, result)

    def do_POST(self):
        """
        Create admin-managed user accounts from authenticated JSON requests.
        """
        log.info("Received HTTP POST request: %s", self.path)

        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 <= length <= MAX_BODY_SIZE:
                raise ValueError("invalid Content-Length")
            raw_body = self.rfile.read(length)
        except ValueError:
            self.send_error(400, "Bad Request", "invalid Content-Length")
            return

        with self.session_lock:
            if not self.authenticate_request(raw_body):
                return

            if self.api_path() != ADMIN_USERS_PATH:
                self.send_error(404)
                return

            try:
                obj = json.loads(raw_body.decode("utf-8"))
                username = obj["username"]
                password = obj["password"]

                if not isinstance(username, str) or not username:
                    raise ValueError("invalid username")
                if not isinstance(password, str) or not password:
                    raise ValueError("invalid password")

                result = self.peer_service.create_user(
                    username,
                    password,
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ):
                self.send_error(
                    400,
                    "Bad Request",
                    "Invalid account request",
                )
                return
            except WGPeerError as exc:
                self.send_error(
                    exc.status,
                    "Peer service error",
                    exc.message,
                )
                return

            self.send_json(201, result)

    def do_DELETE(self):
        """
        Handle session logout, admin account deletion and peer deletion.
        """
        log.warning("Received HTTP DELETE request: %s", self.path)

        with self.session_lock:
            if not self.authenticate_request(b""):
                return

            path = self.api_path()

            if path == SESSION_PATH:
                self.send_json(200, {"ok": True})
                self.server.lifecycle.request_shutdown()
                return

            if path is not None and path.startswith(ADMIN_USERS_PREFIX):
                username = unquote(path[len(ADMIN_USERS_PREFIX):])
                if not username:
                    self.send_error(404)
                    return

                try:
                    result = self.peer_service.delete_user(username)
                except WGPeerError as exc:
                    self.send_error(
                        exc.status,
                        "Peer service error",
                        exc.message,
                    )
                    return

                self.send_json(200, result)
                return

            public_key = self.peer_key(path)
            if public_key is None:
                self.send_error(404)
                return

            try:
                result = self.peer_service.remove_peer(public_key)
            except WGPeerError as exc:
                self.send_error(
                    exc.status,
                    "Peer service error",
                    exc.message,
                )
                return

            self.send_json(200, result)

    def do_CONNECT(self):
        """
        Reject CONNECT with HTTP 405.
        """
        log.warning("Received HTTP CONNECT request: %s", self.path)
        self.send_error(405)

    def do_PATCH(self):
        """
        Reject PATCH with HTTP 405.
        """
        log.warning("Received HTTP PATCH request: %s", self.path)
        self.send_error(405)

    def do_PUT(self):
        """
        Handle peer creation and admin ownership reassignment.
        """
        log.warning("Received HTTP PUT request: %s", self.path)

        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 <= length <= MAX_BODY_SIZE:
                raise ValueError("invalid Content-Length")
            raw_body = self.rfile.read(length)
        except ValueError:
            self.send_error(400, "Bad Request", "invalid Content-Length")
            return

        with self.session_lock:
            if not self.authenticate_request(raw_body):
                return

            path = self.api_path()
            admin_public_key = self.admin_owner_key(path)

            if admin_public_key is not None:
                try:
                    obj = json.loads(raw_body.decode("utf-8"))
                    username = obj["username"]

                    if not isinstance(username, str) or not username:
                        raise ValueError("invalid username")

                    result = self.peer_service.reassign_owner(
                        admin_public_key,
                        username,
                    )

                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    self.send_error(
                        400,
                        "Bad Request",
                        "Invalid ownership request",
                    )
                    return

                except WGPeerError as exc:
                    self.send_error(
                        exc.status,
                        "Peer service error",
                        exc.message,
                    )
                    return

                self.send_json(200, result)
                return

            public_key = self.peer_key(path)
            if public_key is None:
                self.send_error(404)
                return

            try:
                obj = json.loads(raw_body.decode("utf-8"))
                allowed_ip = obj["allowed_ip"]
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ):
                self.send_error(
                    400,
                    "Bad Request",
                    "Invalid peer request",
                )
                return

            try:
                result = self.peer_service.add_peer(
                    public_key,
                    allowed_ip,
                )
            except WGPeerError as exc:
                self.send_error(
                    exc.status,
                    "Peer service error",
                    exc.message,
                )
                return

            self.send_json(200, result)

