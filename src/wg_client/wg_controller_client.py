#!/usr/bin/env python3

"""
HTTPS client adapters used by wg-client and integration tests.

WGControllerClient is the production mTLS client for the privileged controller.
WGClientClient targets the per-session wg-client API and can add WGSecureSession
request/response authentication when supplied.
"""

import http.client
import json
import ssl
from urllib.parse import quote
import logging

from src.wg_client.wg_client_errors import WGControllerError
from src.wg_version import PACKAGE_VERSION, PROTOCOL_VERSION_HEADER
from src.wg_client.wg_client_API_handler import AUTH_SESSION_ID_HEADER, AUTH_COUNTER_HEADER, AUTH_NONCE_HEADER, AUTH_MAC_HEADER


class WGControllerClient:
    """
    Small mTLS JSON client for the privileged wg-manager controller API.
    """
    def __init__(self, host, port, ca, cert, key, timeout=10):
        """
        Build a TLS 1.3 client context with CA verification and a client certificate.
        """
        self.host = host
        self.port = port
        self.timeout = timeout

        self.tls = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca)

        self.tls.minimum_version = ssl.TLSVersion.TLSv1_3
        self.tls.load_cert_chain(certfile=cert, keyfile=key)

    def _request(self, method, path, body=None):
        if body is None:
            data = None
        elif isinstance(body, bytes):
            data = body
        else:
            data = json.dumps(body, separators=(",", ":")).encode()

        conn = http.client.HTTPSConnection(
            self.host, self.port, context=self.tls, timeout=self.timeout
        )

        headers = {
            "Accept": "application/json",
            "Connection": "close",
            PROTOCOL_VERSION_HEADER: PACKAGE_VERSION,
        }

        if data is not None:
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(data))

        try:
            try:
                conn.request(method, path, body=data, headers=headers)

                response = conn.getresponse()
                raw = response.read()

                remote_version = response.getheader(PROTOCOL_VERSION_HEADER)
                if remote_version != PACKAGE_VERSION:
                    raise WGControllerError(
                        502,
                        "controller protocol version mismatch: "
                        f"expected {PACKAGE_VERSION}, got "
                        f"{remote_version or 'missing'}",
                    )

            # ssl.SSLError and TimeoutError are subclasses of OSError.
            except (OSError, http.client.HTTPException) as exc:
                raise WGControllerError(
                    502, f"controller unreachable: {type(exc).__name__}"
                ) from exc

            try:
                obj = json.loads(raw.decode())
            except (UnicodeDecodeError, json.JSONDecodeError):
                obj = None

            if response.status >= 400:
                message = "HTTP error"

                if isinstance(obj, dict):
                    message = obj.get("error", message)

                raise WGControllerError(response.status, message, obj)

            return response.status, obj

        finally:
            conn.close()

    def status(self):
        """
        Return the controller /v1/status document.
        """
        status, obj = self._request("GET", "/v1/status")

        return obj

    def provisioning(self):
        """
        Return controller provisioning metadata for client configuration generation.
        """
        status, obj = self._request("GET", "/v1/provisioning")
        return obj

    def add_peer(self, public_key, allowed_ip):
        """
        Create a controller peer from public key and allowed IP.
        """
        status, obj = self._request(
            "POST",
            "/v1/peers",
            {
                "public_key": str(public_key),
                "allowed_ip": str(allowed_ip),
            },
        )

        return obj

    def remove_peer(self, public_key):
        """
        Remove one controller peer by public key.
        """
        path = "/v1/peers/" + quote(public_key, safe="")

        status, obj = self._request("DELETE", path)

        return obj


class WGClientClient:
    """
    HTTP client for a per-session wg-client API, optionally using WGSecureSession.
    """
    def __init__(self, host, port, ca, cert, key, timeout=10,listen_path=None,secure_session=None):
        """
        Configure TLS, optional listen-path prefix and optional secure-session authentication.
        """
        self.log = logging.getLogger("wg_client.ClientClient")
        self.host = host
        self.port = port
        self.timeout = timeout

        self.tls = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca)

        self.tls.minimum_version = ssl.TLSVersion.TLSv1_3
        self.tls.load_cert_chain(certfile=cert, keyfile=key)

        self.listen_path = listen_path
        self.secure_session = secure_session
        if secure_session is None:
            self.log.warning("secure_session is None, using insecure session")

    def _request(self, method, path, body=None):
        if body is None:
            data = None
        elif isinstance(body, bytes):
            data = body
        else:
            data = json.dumps(body, separators=(",", ":")).encode()

        conn = http.client.HTTPSConnection(
            self.host, self.port, context=self.tls, timeout=self.timeout
        )
        headers = {
            "Accept": "application/json",
            "Connection": "close",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(data))

        if self.secure_session is not None:
            auth_path= str(path)
            req_auth = self.secure_session.create_request_auth(
                method,
                auth_path,
                data or b""
            )
            headers.update({
                AUTH_SESSION_ID_HEADER: req_auth["session_id"],
                AUTH_COUNTER_HEADER: str(req_auth["counter"]),
                AUTH_NONCE_HEADER: req_auth["nonce"],
                AUTH_MAC_HEADER: req_auth["mac"],
            })

        request_path = (
            f"{self.listen_path}{path}"
            if self.listen_path is not None
            else str(path)
        )

        try:
            try:
                conn.request(method, request_path, body=data, headers=headers)
                response = conn.getresponse()
                raw = response.read()
            # ssl.SSLError and TimeoutError are subclasses of OSError.
            except (OSError, http.client.HTTPException) as exc:
                raise WGControllerError(
                    502, f"controller unreachable: {type(exc).__name__}"
                ) from exc
            try:
                if self.secure_session is not None:
                    response_auth = {
                        "session_id": response.getheader(AUTH_SESSION_ID_HEADER),
                        "counter": int(response.getheader(AUTH_COUNTER_HEADER)),
                        "mac": response.getheader(AUTH_MAC_HEADER),
                    }
                    self.secure_session.verify_response(
                        response_auth,
                        req_auth,
                        response.
                        status,
                        raw
                    )
                obj = json.loads(raw.decode())
            except (UnicodeDecodeError, json.JSONDecodeError):
                obj = None
            if response.status >= 400:
                message = "HTTP error"
                if isinstance(obj, dict):
                    message = obj.get("error", message)
                raise WGControllerError(response.status, message, obj)
            return response.status, obj
        finally:
            conn.close()

    def status(self):
        """
        Return the per-session /v1/status document.
        """
        status, obj = self._request("GET", "/v1/status")

        return obj

    def add_peer(self, public_key, allowed_ip):
        """
        Add a peer through the authenticated wg-client API.
        """
        status, obj = self._request(
            "PUT",
            "/v1/peers/" + quote(public_key, safe=""),
            {
                "public_key": str(public_key),
                "allowed_ip": str(allowed_ip),
            },
        )

        return obj

    def remove_peer(self, public_key):
        """
        Remove a peer through the authenticated wg-client API.
        """
        path = "/v1/peers/" + quote(public_key, safe="")

        status, obj = self._request("DELETE", path)

        return obj
