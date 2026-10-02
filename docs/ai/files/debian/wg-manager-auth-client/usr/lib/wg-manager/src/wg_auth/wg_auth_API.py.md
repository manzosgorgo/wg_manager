# `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_API.py`

## Metadata

- Path: `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_API.py`
- Language: `python`
- Lines: 433
- SHA256: `97bd584f59c9bb8c638c56143c35fbeb1020cbb19cfeff11835b4ac5084159bf`
- Imports:
  - `http.server`
  - `json`
  - `logging`
  - `src.wg_auth.wg_auth_API_handler`
  - `src.wg_auth.wg_auth_IPC`
  - `src.wg_auth.wg_auth_account_service`
  - `src.wg_auth.wg_auth_errors`
  - `src.wg_auth.wg_auth_ownership_service`
  - `src.wg_auth.wg_auth_peer_registry`
  - `src.wg_auth.wg_auth_session`
  - `src.wg_auth.wg_auth_user_store`
  - `ssl`
  - `threading`

## Source

```python
import ssl
import json
import logging
import threading
from http.server import ThreadingHTTPServer

from src.wg_auth.wg_auth_IPC import WGAuthIPC
from src.wg_auth.wg_auth_errors import WGAuthSessionError, WGAuthAuthenticationError
from src.wg_auth.wg_auth_user_store import WGAuthUserStore
from src.wg_auth.wg_auth_peer_registry import WGAuthPeerRegistry
from src.wg_auth.wg_auth_ownership_service import WGAuthOwnershipService
from src.wg_auth.wg_auth_account_service import WGAuthAccountService

log = logging.getLogger("wg_auth.API")


class WGAuthAPI:
    SESSION_IDLE = "IDLE"
    SESSION_STARTING = "STARTING"
    SESSION_ACTIVE = "ACTIVE"
    SESSION_STOPPING = "STOPPING"

    def __init__(self, config, lifecycle):
        self.config = config
        self.lifecycle = lifecycle
        self.user_store = WGAuthUserStore(config["auth"]["login_dir"])
        self.peer_registry = WGAuthPeerRegistry(
            config["auth"].get(
                "peer_registry",
                config["auth"]["login_dir"] + "/.peer_registry.json",
            ),
            config["auth"].get(
                "ip_registry",
                config["auth"]["login_dir"] + "/.ip_registry.json",
            ),
        )
        self.ownership_service = WGAuthOwnershipService(
            self.user_store,
            self.peer_registry,
        )
        self.account_service = WGAuthAccountService(
            self.user_store,
        )

        self.session = None
        self.ipc = None
        self.server = None

        # Protects session/ipc/session_state.
        self.session_lock = threading.RLock()

        self.session_state = self.SESSION_IDLE

        # Used when logout happens while activation is still in progress.
        self.session_stop_requested = False

    def __enter__(self):
        self.server = self._create_server()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def run(self):
        if self.server is None:
            raise RuntimeError("API server is not started")

        self.server.serve_forever()

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    # ------------------------------------------------------------------
    # Session state
    # ------------------------------------------------------------------

    def get_session_status(self):
        with self.session_lock:
            state = self.session_state

            return {
                "authenticated": state == self.SESSION_ACTIVE,
                "client_active": (
                    state == self.SESSION_ACTIVE
                    and self.ipc is not None
                    and self.ipc.active
                ),
            }

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def start_authentication(self, username, pubU):
        from src.wg_auth.wg_auth_session import WGAuthSession

        with self.session_lock:
            if self.session_state != self.SESSION_IDLE:
                raise WGAuthSessionError(
                    "session already active"
                )

            try:
                user = self.user_store.load(username)
            except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
                raise WGAuthAuthenticationError(
                    "authentication failed"
                )

            session = WGAuthSession(
                username=user.username,
                credential_record=user.credential_record,
                context=b"wg-manager",
                principal=user.principal,
            )

            response = session.create_credential_response(pubU)

            self.session = session
            self.ipc = None
            self.session_state = self.SESSION_STARTING
            self.session_stop_requested = False

            log.debug(
                "OPAQUE authentication started for %r",
                username,
            )

            return response


    def finish_authentication(self, authU):
        with self.session_lock:
            if self.session_state != self.SESSION_STARTING:
                raise WGAuthSessionError(
                    "authentication is not in progress"
                )

            session = self.session

            if session is None:
                raise WGAuthSessionError(
                    "authentication session missing"
                )

        # OPAQUE verification does not require the API lock.
        session.authenticate(authU)

        with self.session_lock:
            if (
                    self.session is not session
                    or self.session_state != self.SESSION_STARTING
            ):
                session.logout()
                raise WGAuthSessionError(
                    "authentication session was stopped"
                )

            ipc = WGAuthIPC(
                socket_path=self.config["client"]["socket_path"],
                client_id=self.config["client"]["client_id"],
                timeout=int(self.config["client"]["timeout"]),
                listen_path=self.config["client"]["listen_path"],
                lifecycle=self.lifecycle,
                principal=session.principal,
                peer_register=self._register_peer,
                peer_unregister=self._unregister_peer,
                state_reconcile=self._reconcile_peer_state,
                provisioning_state=self._provisioning_state,
                ownership_state=self._ownership_state,
                ownership_reassign=self._reassign_ownership,
                account_create=self._create_account,
                account_delete=self._delete_account,
            )

            self.ipc = ipc

            self.session_state = self.SESSION_STARTING

            self.lifecycle.ipc = ipc

            log.debug(
                "OPAQUE authentication successful; "
                "activating wg-client"
            )

        try:
            response = ipc.activate(
                session.session_id,
                session.k_session,
            )

        except Exception as exc:
            log.exception(f"failed to activate wg-client with status:{exc}")
            self._activation_failed(session, ipc)
            raise

        with self.session_lock:
            stop_requested = (
                    self.session_stop_requested
                    or self.session_state == self.SESSION_STOPPING
            )

            if (
                    self.session is not session
                    or self.ipc is not ipc
            ):
                stop_requested = True

            if stop_requested:
                self.session_state = self.SESSION_STOPPING
            else:
                self.session_state = self.SESSION_ACTIVE
                log.info("session became ACTIVE")

        if stop_requested:
            self._finish_shutdown(session, ipc)

            raise WGAuthSessionError(
                "session was stopped during activation"
            )

        self.lifecycle.request_session_start()

        return response



    def _register_peer(self, username, public_key, allowed_ip):
        self.peer_registry.reserve(
            username,
            public_key,
            allowed_ip,
        )

        try:
            self.user_store.add_peer(username, public_key)
        except Exception:
            self.peer_registry.release(username, public_key)
            raise

    def _unregister_peer(self, username, public_key):
        reservation = self.peer_registry.release(
            username,
            public_key,
        )

        owner = (
            reservation["username"]
            if reservation is not None
            else username
        )

        if owner is not None:
            self.user_store.remove_peer(owner, public_key)

    def _reconcile_peer_state(self, manager_peers):
        owners = self.user_store.peer_owners()
        return self.peer_registry.reconcile(
            manager_peers,
            owners,
        )

    def _provisioning_state(self):
        return {
            "reserved_ips": sorted(
                self.peer_registry.snapshot_ips().keys()
            ),
        }

    def _ownership_state(self):
        return self.ownership_service.admin_state()

    def _reassign_ownership(self, public_key, username):
        return self.ownership_service.reassign(
            public_key,
            username,
        )

    def _create_account(self, username, password):
        return self.account_service.create(
            username,
            password,
        )

    def _delete_account(self, username):
        return self.account_service.delete(
            username,
        )

    # ------------------------------------------------------------------
    # Activation failure
    # ------------------------------------------------------------------

    def _activation_failed(self, session, ipc):
        with self.session_lock:
            if self.session is session:
                self.session = None

            if self.ipc is ipc:
                self.ipc = None

            self.session_state = self.SESSION_IDLE
            self.session_stop_requested = False

            if self.lifecycle.ipc is ipc:
                self.lifecycle.ipc = None

        session.logout()
        ipc.close()

        log.info("session activation failed; state returned to IDLE")

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def logout(self, notify_client=True):
        with self.session_lock:
            if self.session_state == self.SESSION_IDLE:
                return

            session = self.session
            ipc = self.ipc

            # ----------------------------------------------------------
            # If activation is currently running, do not attempt to
            # race it. Mark the transition for cancellation.
            # ----------------------------------------------------------

            if self.session_state == self.SESSION_STARTING:
                self.session_stop_requested = True
                self.session_state = self.SESSION_STOPPING

                log.info(
                    "logout requested while session is STARTING"
                )

                return

            # ----------------------------------------------------------
            # ACTIVE -> STOPPING
            # ----------------------------------------------------------

            self.session_state = self.SESSION_STOPPING

            self.session = None
            self.ipc = None

            if self.lifecycle.ipc is ipc:
                self.lifecycle.ipc = None

        self._finish_shutdown(
            session,
            ipc,
            notify_client=notify_client,
        )

    # ------------------------------------------------------------------
    # Final cleanup
    # ------------------------------------------------------------------

    def _finish_shutdown(
        self,
        session,
        ipc,
        notify_client=True,
    ):
        if ipc is not None:
            try:
                if notify_client:
                    ipc.deactivate()
                else:
                    ipc.close()
            except Exception:
                log.exception("error while shutting down IPC")
                ipc.close()

        if session is not None:
            session.logout()

        with self.session_lock:
            # Only clear state if this is still the same transition.
            if self.session is None and self.ipc is None:
                self.session_state = self.SESSION_IDLE
                self.session_stop_requested = False

        log.info("session returned to IDLE")

    # ------------------------------------------------------------------
    # HTTP server
    # ------------------------------------------------------------------

    def _create_server(self):
        from src.wg_auth.wg_auth_API_handler import WGAuthAPIHandler

        WGAuthAPIHandler.api = self

        server = ThreadingHTTPServer(
            (
                self.config["http"]["host"],
                int(self.config["http"]["port"]),
            ),
            WGAuthAPIHandler,
        )

        context = ssl.SSLContext(
            ssl.PROTOCOL_TLS_SERVER
        )

        context.load_cert_chain(
            self.config["http"]["server_cert"],
            self.config["http"]["server_key"],
        )

        if self.config["http"].getboolean(
            "require_client_cert"
        ):
            context.verify_mode = ssl.CERT_REQUIRED

            context.load_verify_locations(
                self.config["http"]["ca_cert"]
            )

        server.socket = context.wrap_socket(
            server.socket,
            server_side=True,
        )

        return server
```
