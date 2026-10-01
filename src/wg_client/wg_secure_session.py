#!/usr/bin/env python3

import base64
import binascii
import hashlib
import hmac
import logging
import math
import secrets
import threading
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from src.wg_client.wg_client_errors import (
    WGMalformedMessageError,
    WGInvalidFieldError,
    WGInvalidEncodingError,
    WGCounterError,
    WGCounterExhaustedError,
    WGReplayError,
    WGSessionExpiredError,
    WGRequestRateExceededError,
    WGSessionMismatchError,
    WGInvalidMACError,
)

log = logging.getLogger("wg_manager.secure_session")


class WGSecureSession:
    """
    Cryptographic state for a wg_manager session.

    The caller supplies the shared K_session established during
    the authentication phase.

    K_session itself is never transmitted by this class.
    """

    PROTOCOL_VERSION = b"wg_manager secure session v1"

    session_id_size = 16
    nonce_size = 32
    key_size = 32

    # MAC size is a property of the algorithm (HMAC-SHA256), not
    # something that should be configurable.
    MAC_SIZE = hashlib.sha256().digest_size

    def __init__(
            self,
            config,
            k_session: bytes,
            session_id: bytes | None = None,
            rng=None,
            clock=None,
    ):
        log.info("initializing WGSecureSession")
        self.config = config

        self.session_id_size = config["secure_session"]["session_id_size"]
        self.nonce_size = config["secure_session"]["nonce_size"]
        self.key_size = config["secure_session"]["session_key_size"]
        self.counter_min = config["secure_session"]["counter_min"]

        if self.counter_min < 1:
            raise WGInvalidFieldError("invalid counter minimum")

        self.counter_max = config["secure_session"]["counter_max"]
        if self.counter_max < self.counter_min:
            raise WGInvalidFieldError("invalid counter range")

        if self.counter_max > 0xFFFFFFFF:
            raise WGInvalidFieldError("counter maximum exceeds uint32 range")

        secure_config = config["secure_session"]
        self.session_timeout = secure_config.get("session_timeout", 86400)
        self.max_request_frequency = secure_config.get(
            "max_request_frequency", 0.0
        )
        self.replay_window_size = secure_config.get("replay_window_size", 64)

        if self.session_timeout <= 0:
            raise WGInvalidFieldError("invalid session timeout")

        if (
            not math.isfinite(self.max_request_frequency)
            or self.max_request_frequency < 0
        ):
            raise WGInvalidFieldError("invalid maximum request frequency")

        if self.replay_window_size <= 0:
            raise WGInvalidFieldError("invalid replay window size")

        counter_capacity = self.counter_max - self.counter_min + 1
        if (
            self.max_request_frequency > 0
            and self.max_request_frequency * self.session_timeout
            > counter_capacity
        ):
            raise WGInvalidFieldError(
                "maximum request frequency and session timeout exceed "
                "the secure session counter capacity"
            )

        if not isinstance(k_session, bytes):
            log.warning("k_session must be bytes")
            raise WGInvalidFieldError("k_session must be bytes")

        if len(k_session) != self.key_size:
            log.warning("k_session must be %d bytes", self.key_size)
            raise WGInvalidFieldError(
                f"k_session must be {self.key_size} bytes"
            )

        if session_id is None:
            session_id = secrets.token_bytes(self.session_id_size)

        if not isinstance(session_id, bytes):
            log.warning("session_id must be bytes")
            raise WGInvalidFieldError("session_id must be bytes")

        if len(session_id) != self.session_id_size:
            log.warning("session_id must be %d bytes", self.session_id_size)
            raise WGInvalidFieldError(
                f"session_id must be {self.session_id_size} bytes"
            )

        self._k_session = k_session
        self._session_id = session_id

        self._session_seed = self._derive_session_seed()

        self._request_key = self._derive_key(b"request authentication")

        self._response_key = self._derive_key(b"response authentication")

        self._request_counter = self.counter_min - 1
        self._pending_requests = {}

        self._request_receive_highest = self.counter_min - 1
        self._request_receive_accepted = set()
        self._response_receive_highest = self.counter_min - 1
        self._response_receive_accepted = set()

        self._clock = clock or time.monotonic
        self._session_started = self._clock()
        self._session_expires_at = self._session_started + self.session_timeout

        self._rng = rng or secrets.token_bytes

        # Protects all mutable session state. Counter allocation, replay
        # checks and lifecycle policy decisions must be atomic when the
        # instance is shared by threads.
        self._lock = threading.Lock()
    # ------------------------------------------------------------------
    # Public session information
    # ------------------------------------------------------------------

    @property
    def session_id(self) -> bytes:
        log.debug("session_id property")
        return self._session_id

    @property
    def session_id_b64(self) -> str:
        log.debug("session_id_b64 property")
        return self._b64(self._session_id)

    # ------------------------------------------------------------------
    # Key derivation
    # ------------------------------------------------------------------

    def _derive_session_seed(self) -> bytes:
        log.debug("derivation of session seed")
        return HKDF(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=self._session_id,
            info=self.PROTOCOL_VERSION,
        ).derive(self._k_session)

    def _derive_key(self, purpose: bytes) -> bytes:
        log.debug("derivation of session key")
        return HKDF(
            algorithm=hashes.SHA256(),
            length=self.key_size,
            salt=None,
            info=self.PROTOCOL_VERSION + b"|" + purpose,
        ).derive(self._session_seed)

    # ------------------------------------------------------------------
    # Request authentication
    # ------------------------------------------------------------------

    def create_request_auth(
        self,
        method: str,
        path: str,
        body: bytes = b"",
    ) -> dict:
        """
        Create authentication parameters for a new request.

        Thread-safe: concurrent callers never obtain the same counter.
        """
        with self._lock:
            return self._create_request_auth_unlocked(method, path, body)

    def _create_request_auth_unlocked(
        self,
        method: str,
        path: str,
        body: bytes = b"",
    ) -> dict:
        """
        Create authentication parameters for a new request.
        """
        log.debug("Create authentication parameters for a new request")

        if not isinstance(method, str):
            log.warning("method must be str")
            raise WGInvalidFieldError("method must be str")

        if not isinstance(path, str):
            log.warning("path must be str")
            raise WGInvalidFieldError("path must be str")

        if not isinstance(body, bytes):
            log.warning("body must be bytes")
            raise WGInvalidFieldError("body must be bytes")

        self._check_session_active_unlocked()

        if self._request_counter >= self.counter_max:
            log.warning("request counter exhausted")
            raise WGCounterExhaustedError("request counter exhausted")

        self._check_request_rate_unlocked()

        counter = self._request_counter + 1
        nonce = self._rng(self.nonce_size)

        message = self._request_message(
            counter,
            nonce,
            method,
            path,
            body,
        )

        mac = hmac.digest(
            self._request_key,
            message,
            hashlib.sha256,
        )

        self._request_counter = counter

        auth = {
            "session_id": self.session_id_b64,
            "counter": counter,
            "nonce": self._b64(nonce),
            "mac": self._b64(mac),
        }
        self._pending_requests[counter] = dict(auth)
        return auth

    # ------------------------------------------------------------------
    # Response authentication
    # ------------------------------------------------------------------

    def create_response_auth(
        self,
        request_auth: dict,
        status: int,
        body: bytes = b"",
    ) -> dict:
        """
        Create authentication parameters for a response.
        """
        with self._lock:
            return self._create_response_auth_unlocked(
                request_auth, status, body
            )

    def _create_response_auth_unlocked(
        self,
        request_auth: dict,
        status: int,
        body: bytes = b"",
    ) -> dict:
        """
        Create authentication parameters for a response.
        """
        log.debug("Create authentication parameters for a response")

        self._check_session_active_unlocked()

        if not isinstance(status, int) or isinstance(status, bool):
            log.warning("status must be int")
            raise WGInvalidFieldError("status must be int")

        if not isinstance(body, bytes):
            log.warning("body must be bytes")
            raise WGInvalidFieldError("body must be bytes")

        validated_request = self._validate_request_auth(request_auth)

        if validated_request["session_id"] != self._session_id:
            log.warning("invalid session id")
            raise WGSessionMismatchError("invalid session id")

        counter = validated_request["counter"]
        nonce = validated_request["nonce"]

        message = self._response_message(
            counter,
            nonce,
            status,
            body,
        )

        mac = hmac.digest(
            self._response_key,
            message,
            hashlib.sha256,
        )

        return {
            "session_id": self.session_id_b64,
            "counter": counter,
            "mac": self._b64(mac),
        }

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_request(
        self,
        auth: dict,
        method: str,
        path: str,
        body: bytes = b"",
    ) -> bool:
        """
        Verify request authentication.

        Thread-safe: the replay check and the counter update are one
        atomic step, so a request is accepted at most once.
        """
        with self._lock:
            return self._verify_request_unlocked(auth, method, path, body)

    def _verify_request_unlocked(
        self,
        auth: dict,
        method: str,
        path: str,
        body: bytes = b"",
    ) -> bool:
        """
        Verify request authentication.

        The request counter must be inside the replay window and must
        not have been accepted before.
        """
        log.debug("Verify request authentication")

        self._check_session_active_unlocked()

        if not isinstance(method, str):
            log.warning("method must be str")
            raise WGInvalidFieldError("method must be str")

        if not isinstance(path, str):
            log.warning("path must be str")
            raise WGInvalidFieldError("path must be str")

        if not isinstance(body, bytes):
            log.warning("body must be bytes")
            raise WGInvalidFieldError("body must be bytes")

        validated = self._validate_request_auth(auth)

        if validated["session_id"] != self._session_id:
            log.warning("invalid session id")
            raise WGSessionMismatchError("invalid session id")

        counter = validated["counter"]

        if not self._counter_in_receive_window_unlocked(
            counter,
            self._request_receive_highest,
        ):
            log.warning("request counter outside replay window")
            raise WGReplayError("request counter outside replay window")

        if counter in self._request_receive_accepted:
            log.warning("request counter replayed")
            raise WGReplayError("request counter replayed")

        nonce = validated["nonce"]
        received_mac = validated["mac"]

        message = self._request_message(
            counter,
            nonce,
            method,
            path,
            body,
        )

        expected_mac = hmac.digest(
            self._request_key,
            message,
            hashlib.sha256,
        )

        if not hmac.compare_digest(
            received_mac,
            expected_mac,
        ):
            log.error("invalid request MAC")
            raise WGInvalidMACError("invalid request MAC")

        self._accept_receive_counter_unlocked(
            counter,
            request=True,
        )

        return True

    def verify_response(
        self,
        auth: dict,
        request_auth: dict,
        status: int,
        body: bytes = b"",
    ) -> bool:
        """
        Verify authentication of a server response.

        Thread-safe: a response is accepted at most once.
        """
        with self._lock:
            return self._verify_response_unlocked(
                auth, request_auth, status, body
            )

    def _verify_response_unlocked(
        self,
        auth: dict,
        request_auth: dict,
        status: int,
        body: bytes = b"",
    ) -> bool:
        """
        Verify authentication of a server response.
        """
        log.debug("Verify authentication of a server response")

        self._check_session_active_unlocked()

        if not isinstance(status, int) or isinstance(status, bool):
            log.warning("status must be int")
            raise WGInvalidFieldError("status must be int")

        if not isinstance(body, bytes):
            log.warning("body must be bytes")
            raise WGInvalidFieldError("body must be bytes")

        validated_auth = self._validate_response_auth(auth)
        validated_request = self._validate_request_auth(request_auth)

        if validated_request["session_id"] != self._session_id:
            log.warning("invalid request session id")
            raise WGSessionMismatchError("invalid request session id")

        if validated_auth["session_id"] != self._session_id:
            log.warning("invalid response session id")
            raise WGSessionMismatchError("invalid response session id")

        if validated_auth["session_id"] != validated_request["session_id"]:
            log.warning("request/response session mismatch")
            raise WGSessionMismatchError("request/response session mismatch")

        if validated_auth["counter"] != validated_request["counter"]:
            log.warning("invalid request counter")
            raise WGCounterError("response counter does not match request")

        counter = validated_auth["counter"]

        if not self._counter_in_receive_window_unlocked(
            counter,
            self._response_receive_highest,
        ):
            log.warning("response counter outside replay window")
            raise WGReplayError("response counter outside replay window")

        if counter in self._response_receive_accepted:
            log.warning("response counter replayed")
            raise WGReplayError("response replayed")

        pending = self._pending_requests.get(counter)
        if pending is None:
            log.warning("response does not correspond to a pending request")
            raise WGCounterError("response does not correspond to a pending request")

        nonce = validated_request["nonce"]
        received_mac = validated_auth["mac"]

        message = self._response_message(
            counter,
            nonce,
            status,
            body,
        )

        expected_mac = hmac.digest(
            self._response_key,
            message,
            hashlib.sha256,
        )

        if not hmac.compare_digest(
            received_mac,
            expected_mac,
        ):
            log.error("invalid response MAC")
            raise WGInvalidMACError("invalid response MAC")

        self._accept_receive_counter_unlocked(
            counter,
            request=False,
        )
        del self._pending_requests[counter]

        return True

    # ------------------------------------------------------------------
    # Session lifecycle and replay windows
    # ------------------------------------------------------------------

    def _check_session_active_unlocked(self):
        if self._clock() >= self._session_expires_at:
            log.warning("secure session expired")
            raise WGSessionExpiredError("secure session expired")

    def _check_request_rate_unlocked(self):
        if self.max_request_frequency <= 0:
            return

        elapsed = max(0.0, self._clock() - self._session_started)
        requests_used = self._request_counter - self.counter_min + 1
        allowed = math.floor(elapsed * self.max_request_frequency) + 1

        if requests_used >= allowed:
            log.warning("maximum request frequency exceeded")
            raise WGRequestRateExceededError(
                "maximum request frequency exceeded"
            )

    def _counter_in_receive_window_unlocked(self, counter, highest_seen):
        lower_bound = max(
            self.counter_min,
            highest_seen - self.replay_window_size + 1,
        )
        return lower_bound <= counter <= self.counter_max

    def _accept_receive_counter_unlocked(self, counter, request):
        if request:
            accepted = self._request_receive_accepted
            highest = self._request_receive_highest
        else:
            accepted = self._response_receive_accepted
            highest = self._response_receive_highest

        if counter > highest:
            highest = counter

        accepted.add(counter)
        lower_bound = max(
            self.counter_min,
            highest - self.replay_window_size + 1,
        )
        expired = {value for value in accepted if value < lower_bound}
        accepted.difference_update(expired)
        if request:
            self._request_receive_highest = highest
        else:
            self._response_receive_highest = highest

    # ------------------------------------------------------------------
    # Field validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_auth_structure(auth: dict, required_fields: tuple) -> None:
        log.debug("Validate auth structure")

        if not isinstance(auth, dict):
            raise WGMalformedMessageError("auth must be a dict")

        for field in required_fields:
            if field not in auth:
                raise WGMalformedMessageError(f"missing field: {field}")

    def _validate_session_id(self, value) -> bytes:
        session_id = self._unb64(value)

        if len(session_id) != self.session_id_size:
            raise WGInvalidFieldError(
                f"session_id must be {self.session_id_size} bytes"
            )

        return session_id

    def _validate_counter(self, value) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise WGInvalidFieldError("counter must be int")

        if value < self.counter_min or value > self.counter_max:
            raise WGCounterError("counter out of valid range")

        return value

    def _validate_nonce(self, value) -> bytes:
        nonce = self._unb64(value)

        if len(nonce) != self.nonce_size:
            raise WGInvalidFieldError(
                f"nonce must be {self.nonce_size} bytes"
            )

        return nonce

    def _validate_mac(self, value) -> bytes:
        mac = self._unb64(value)

        if len(mac) != self.MAC_SIZE:
            raise WGInvalidFieldError(
                f"mac must be {self.MAC_SIZE} bytes"
            )

        return mac

    def _validate_request_auth(self, auth: dict) -> dict:
        log.debug("Validate request auth")

        self._validate_auth_structure(
            auth, ("session_id", "counter", "nonce", "mac")
        )

        return {
            "session_id": self._validate_session_id(auth["session_id"]),
            "counter": self._validate_counter(auth["counter"]),
            "nonce": self._validate_nonce(auth["nonce"]),
            "mac": self._validate_mac(auth["mac"]),
        }

    def _validate_response_auth(self, auth: dict) -> dict:
        log.debug("Validate response auth")

        self._validate_auth_structure(
            auth, ("session_id", "counter", "mac")
        )

        return {
            "session_id": self._validate_session_id(auth["session_id"]),
            "counter": self._validate_counter(auth["counter"]),
            "mac": self._validate_mac(auth["mac"]),
        }

    # ------------------------------------------------------------------
    # Internal serialization
    #
    # NOTE: canonical message serialization (the b"|".join(...) format
    # below) is intentionally left untouched for now. Whether to freeze
    # this format or move to a length-prefixed encoding is a separate
    # piece of work, tackled only once validation/counter/encoding are
    # done and tested.
    # ------------------------------------------------------------------

    def _request_message(
        self,
        counter: int,
        nonce: bytes,
        method: str,
        path: str,
        body: bytes,
    ) -> bytes:
        log.debug("Request message")

        body_hash = hashlib.sha256(body).digest()

        return b"|".join(
            (
                self._session_id,
                str(counter).encode("ascii"),
                nonce,
                method.encode("utf-8"),
                path.encode("utf-8"),
                body_hash,
            )
        )

    def _response_message(
        self,
        counter: int,
        nonce: bytes,
        status: int,
        body: bytes,
    ) -> bytes:
        log.debug("Response message")

        body_hash = hashlib.sha256(body).digest()

        return b"|".join(
            (
                self._session_id,
                str(counter).encode("ascii"),
                nonce,
                str(status).encode("ascii"),
                body_hash,
            )
        )

    # ------------------------------------------------------------------
    # Encoding helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _b64(value: bytes) -> str:
        log.debug("b64 encoding helper")
        return base64.urlsafe_b64encode(value).decode("ascii")

    @staticmethod
    def _unb64(value: str) -> bytes:
        log.debug("unb64 encoding helper")

        if not isinstance(value, str):
            raise WGInvalidFieldError("encoded value must be str")

        try:
            return base64.urlsafe_b64decode(value.encode("ascii"))
        except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
            raise WGInvalidEncodingError("invalid base64 encoding") from exc
