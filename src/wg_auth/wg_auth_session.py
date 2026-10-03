# src/wg_auth/wg_auth_session.py

"""
Server-side OPAQUE authentication state for one login attempt.

The session moves NEW -> AUTHENTICATING -> AUTHENTICATED. Successful OPAQUE
authentication yields a random session identifier and the 64-byte shared
secret exported as hexadecimal for wg-client activation.
"""

import logging
import secrets

import opaque

from src.wg_auth.wg_auth_errors import (
    WGAuthSessionError,
    WGAuthAuthenticationError,
)

log = logging.getLogger("wg-auth")

# python-opaque currently establishes a 64-byte shared session secret.
# Keep this separate from the length of the keys WGSecureSession derives.
OPAQUE_SESSION_KEY_SIZE = 64


class WGAuthSession:
    """
    Own the transient OPAQUE server state and authenticated session secret.
    """

    STATE_NEW = "NEW"
    STATE_AUTHENTICATING = "AUTHENTICATING"
    STATE_AUTHENTICATED = "AUTHENTICATED"

    def __init__(self, username, credential_record, context, principal=None):
        """
        Create a NEW authentication session for one persisted user.
        """
        self.username = username
        self.credential_record = credential_record
        self.context = context
        self.principal = principal or {"username": username, "peers": []}

        self._state = self.STATE_NEW

        self._session_id = None
        self._k_session = None

        # Temporary OPAQUE server-side state.
        self._authU0 = None

    @property
    def authenticated(self):
        """
        Return True only after the OPAQUE proof has been verified.
        """
        return self._state == self.STATE_AUTHENTICATED

    @property
    def session_id(self):
        """
        Return the authenticated session identifier; reject access before authentication.
        """
        if not self.authenticated:
            raise WGAuthSessionError(
                "session is not authenticated"
            )

        return self._session_id

    @property
    def k_session(self):
        """
        Return the OPAQUE shared secret as hex; reject access before authentication.
        """
        if not self.authenticated:
            raise WGAuthSessionError(
                "session is not authenticated"
            )

        return self._k_session

    # ------------------------------------------------------------------
    # OPAQUE authentication
    # ------------------------------------------------------------------

    def create_credential_response(self, pubU):
        """
        Process the client's OPAQUE credential request and enter AUTHENTICATING.
        """
        if self._state != self.STATE_NEW:
            raise WGAuthSessionError(
                "authentication is already in progress"
            )

        if not isinstance(pubU, bytes):
            raise WGAuthAuthenticationError(
                "invalid credential request"
            )

        ids = opaque.Ids(
            self.username.encode("utf-8"),
            b"wg-auth",
        )

        try:
            log.debug(
                "OPAQUE input: pubU=%d bytes, record=%d bytes, context=%d bytes",
                len(pubU),
                len(self.credential_record),
                len(self.context),
            )
            response, sk_server, authU0 = (
                opaque.CreateCredentialResponse(
                    pubU,
                    self.credential_record,
                    ids,
                    self.context,
                )
            )
        except Exception as exc:
            log.error(
                "OPAQUE credential response failed for user %r",
                self.username,
            )
            raise WGAuthAuthenticationError(
                "authentication failed"
            ) from exc

        if not isinstance(sk_server, bytes) or len(sk_server) != OPAQUE_SESSION_KEY_SIZE:
            log.error(
                "unexpected OPAQUE session key size: %r",
                len(sk_server) if isinstance(sk_server, bytes) else type(sk_server),
            )
            raise WGAuthAuthenticationError(
                "unsupported OPAQUE session key"
            )

        self._authU0 = authU0
        self._k_session = sk_server.hex()
        self._state = self.STATE_AUTHENTICATING

        log.debug(
            "OPAQUE authentication started for user %r",
            self.username,
        )

        return response

    def authenticate(self, authU):
        """
        Verify the client OPAQUE authenticator and enter AUTHENTICATED.
        """
        if self._state != self.STATE_AUTHENTICATING:
            raise WGAuthSessionError(
                "authentication is not in progress"
            )

        if not isinstance(authU, bytes):
            raise WGAuthAuthenticationError(
                "authentication failed"
            )

        try:
            opaque.UserAuth(
                self._authU0,
                authU,
            )
        except Exception as exc:
            log.error(
                "OPAQUE authentication failed for user %r",
                self.username,
            )

            self._authU0 = None
            self._k_session = None
            self._state = self.STATE_NEW

            raise WGAuthAuthenticationError(
                "authentication failed"
            ) from exc

        self._authU0 = None

        self._session_id = secrets.token_hex(16)
        self._state = self.STATE_AUTHENTICATED

        log.info(
            "client authenticated as %r",
            self.username,
        )

    def logout(self):
        """
        Erase transient authentication/session state and return to NEW.
        """
        self._state = self.STATE_NEW

        self._session_id = None
        self._k_session = None
        self._authU0 = None
