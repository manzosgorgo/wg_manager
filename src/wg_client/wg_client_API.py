#!/usr/bin/env python3

import logging
import ssl

from src.wg_client.wg_client_API_handler import WGClientAPIHandler, WGClientHTTPServer
from src.wg_client.wg_client_errors import WGAPIError
from src.wg_client.wg_client_lifecycle import WGClientLifecycle
from src.wg_client.wg_controller_client import WGControllerClient
from src.wg_client.wg_peer_service import WGPeerService


log = logging.getLogger("wg_manager.api")
log.setLevel(logging.DEBUG)


class WGClientAPI:
    def __init__(self, config, listen_path, session, lifecycle=None):
        self.server = None
        log.debug("Initializing WGClientAPI")

        log.debug("host")
        self.host = config["api"]["host"]
        log.debug("port")
        self.port = config["api"]["port"]
        log.debug("cert")
        self.certfile = config["api"]["server_cert"]
        log.debug("key")
        self.keyfile = config["api"]["server_key"]
        log.debug("ca")
        self.cafile = config["api"]["ca"]
        log.debug("interface")
        self.interface = config["wireguard"]["interface"]

        # Every endpoint lives below listen_path, e.g.
        # <listen_path>/v1/status.
        self.listen_path = listen_path

        if session is None:
            raise RuntimeError("WGClientAPI requires an authenticated secure session")

        self.session = session

        if lifecycle is None:
            lifecycle = WGClientLifecycle(self)
        elif lifecycle.api is None:
            lifecycle.api = self
        elif lifecycle.api is not self:
            raise RuntimeError(
                "lifecycle is already associated with another WGClientAPI"
            )
        log.debug("lifrcycle")
        self.lifecycle = lifecycle

        log.debug("ControllerClient")
        self.controller = WGControllerClient(
            config["controller"]["host"],
            config["controller"]["port"],
            cert=config["controller"]["client_cert"],
            key=config["controller"]["client_key"],
            ca=config["controller"]["ca"],
            timeout=config["controller"]["timeout"],
        )

        self.peer_service = WGPeerService(
            self.controller,
            self.session,
            self.lifecycle,
            self.interface,
        )

    def start(self):
        """Bind and serve until stop() is called."""
        self.bind()
        self.serve()

    def bind(self):
        """
        Bind the listening socket and set up TLS.

        Raises WGAPIError on failure. After a successful bind()
        the caller must call either serve() or close().
        """
        log.debug("Binding WGClientAPI on %s:%d", self.host, self.port)

        try:
            self.server = WGClientHTTPServer(
                (self.host, self.port),
                WGClientAPIHandler,
                self.peer_service,
                self.listen_path,
                self.session,
                self.lifecycle,
            )

            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            context.minimum_version = ssl.TLSVersion.TLSv1_3

            context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

            context.load_verify_locations(cafile=self.cafile)

            context.verify_mode = ssl.CERT_REQUIRED

            self.server.socket = context.wrap_socket(
                self.server.socket, server_side=True
            )

        except (OSError, ssl.SSLError) as exc:
            self.close()

            raise WGAPIError(f"failed to initialize HTTPS API: {exc}") from exc

        log.info("TLS initialized")

    def serve(self):
        """Serve requests until stop() is called, then close the server."""
        log.info("HTTPS server started")

        try:
            self.server.serve_forever()

        except OSError as exc:
            raise WGAPIError(f"HTTPS server error: {exc}") from exc

        finally:
            self.close()

    def stop(self):
        """
        Make serve() return. Safe to call from another thread.

        Must not be called if serve() will never run: shutdown()
        waits for the serve_forever() loop.
        """
        log.debug("Stopping WGClientAPI")

        server = self.server

        if server is not None:
            server.shutdown()

    def close(self):
        """Release the listening socket."""
        server = self.server
        self.server = None

        if server is not None:
            server.server_close()
