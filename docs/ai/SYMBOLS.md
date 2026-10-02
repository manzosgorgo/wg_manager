# Symbols

Structural symbol index extracted mechanically from source files.

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth.py`

- **variable** `log` — line 12
- **variable** `config_path` — line 13
- **function** `def load_config(path)` — line 18
- **function** `def main()` — line 24

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_API.py`

- **variable** `log` — line 14
- **class** `WGAuthAPI` — line 17
  - **method** `def __init__(self, config, lifecycle)` — line 23
  - **method** `def __enter__(self)` — line 57
  - **method** `def __exit__(self, exc_type, exc_value, traceback)` — line 61
  - **method** `def run(self)` — line 64
  - **method** `def stop(self)` — line 70
  - **method** `def get_session_status(self)` — line 80
  - **method** `def start_authentication(self, username, pubU)` — line 97
  - **method** `def finish_authentication(self, authU)` — line 135
  - **method** `def _register_peer(self, username, public_key, allowed_ip)` — line 232
  - **method** `def _unregister_peer(self, username, public_key)` — line 245
  - **method** `def _reconcile_peer_state(self, manager_peers)` — line 260
  - **method** `def _provisioning_state(self)` — line 267
  - **method** `def _ownership_state(self)` — line 274
  - **method** `def _reassign_ownership(self, public_key, username)` — line 277
  - **method** `def _create_account(self, username, password)` — line 283
  - **method** `def _delete_account(self, username)` — line 289
  - **method** `def _activation_failed(self, session, ipc)` — line 298
  - **method** `def logout(self, notify_client = True)` — line 321
  - **method** `def _finish_shutdown(self, session, ipc, notify_client = True)` — line 366
  - **method** `def _create_server(self)` — line 397

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_API_handler.py`

- **variable** `log` — line 9
- **class** `WGAuthAPIHandler` (BaseHTTPRequestHandler) — line 11
  - **method** `def _send_json(self, status, payload)` — line 14
  - **method** `def _read_json(self)` — line 26
  - **method** `def _handle_auth_start(self)` — line 46
  - **method** `def _handle_auth_verify(self)` — line 118
  - **method** `def do_POST(self)` — line 188
  - **method** `def do_DELETE(self)` — line 202
  - **method** `def do_GET(self)` — line 221

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_IPC.py`

- **variable** `log` — line 8
- **variable** `MAX_PACKET_SIZE` — line 11
- **variable** `PROTOCOL_VERSION` — line 12
- **class** `WGAuthIPC` — line 15
  - **method** `def __init__(self, socket_path, client_id, timeout, listen_path, lifecycle, principal = None, peer_register = None, peer_unregister = None, state_reconcile = None, provisioning_state = None, ownership_state = None, ownership_reassign = None, account_create = None, account_delete = None)` — line 17
  - **method** `def active(self)` — line 52
  - **method** `def control_loop(self)` — line 55
  - **method** `def _handle_peer_request(self, request)` — line 142
  - **method** `def _handle_provisioning_request(self, request)` — line 215
  - **method** `def _handle_ownership_request(self, request)` — line 245
  - **method** `def _handle_account_request(self, request)` — line 332
  - **method** `def receive_packet(self)` — line 426
  - **method** `def parse_packet(self, packet)` — line 461
  - **method** `def activate(self, session_id, k_session)` — line 488
  - **method** `def deactivate(self)` — line 556
  - **method** `def _encode_packet(self, packet)` — line 567
  - **method** `def send_packet(self, packet)` — line 580
  - **method** `def close(self)` — line 583

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_account_service.py`

- **variable** `SERVER_ID` — line 6
- **class** `WGAuthAccountService` — line 9
  - **method** `def __init__(self, user_store)` — line 12
  - **method** `def make_opaque_record(username, password)` — line 16
  - **method** `def create(self, username, password)` — line 45
  - **method** `def delete(self, username)` — line 59

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_errors.py`

- **class** `WGAuthError` (Exception) — line 1
  - **method** `def __init__(self, message)` — line 3
- **class** `WGAuthSessionError` (WGAuthError) — line 8
- **class** `WGAuthAuthenticationError` (WGAuthError) — line 12
- **class** `WGAuthProtocolError` (WGAuthError) — line 16

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_lifecycle.py`

- **variable** `log` — line 4
- **class** `WGAuthLifecycle` — line 7
  - **method** `def __init__(self, api = None, ipc = None, idle_timeout = 45)` — line 9
  - **method** `def _cancel_idle_timer_locked(self)` — line 20
  - **method** `def _arm_idle_timer_locked(self)` — line 27
  - **method** `def _idle_timeout_expired(self)` — line 41
  - **method** `def touch_session(self)` — line 45
  - **method** `def request_shutdown(self)` — line 54
  - **method** `def request_session_shutdown(self, notify_client = True)` — line 70
  - **method** `def request_session_start(self)` — line 83

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_ownership_service.py`

- **class** `WGAuthOwnershipService` — line 3
  - **method** `def __init__(self, user_store, peer_registry)` — line 6
  - **method** `def admin_state(self)` — line 10
  - **method** `def reassign(self, public_key, target_username)` — line 40

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_peer_registry.py`

- **class** `WGAuthPeerRegistry` — line 9
  - **method** `def __init__(self, path, ip_path = None)` — line 12
  - **method** `def _load(self)` — line 24
  - **method** `def _write(self, obj)` — line 71
  - **method** `def _load_ips(self)` — line 78
  - **method** `def _write_path(self, path, obj, prefix)` — line 120
  - **method** `def _write_registries(self, peers_obj, ips_obj)` — line 146
  - **method** `def reserve(self, username, public_key, allowed_ip)` — line 158
  - **method** `def release(self, actor_username, public_key)` — line 199
  - **method** `def get(self, public_key)` — line 226
  - **method** `def snapshot(self)` — line 231
  - **method** `def snapshot_ips(self)` — line 238
  - **method** `def set_owner(self, public_key, username)` — line 245
  - **method** `def reconcile(self, manager_peers, owners)` — line 270

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_session.py`

- **variable** `log` — line 13
- **variable** `OPAQUE_SESSION_KEY_SIZE` — line 17
- **class** `WGAuthSession` — line 20
  - **method** `def __init__(self, username, credential_record, context, principal = None)` — line 26
  - **method** `def authenticated(self)` — line 41
  - **method** `def session_id(self)` — line 45
  - **method** `def k_session(self)` — line 54
  - **method** `def create_credential_response(self, pubU)` — line 66
  - **method** `def authenticate(self, authU)` — line 126
  - **method** `def logout(self)` — line 166

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth_user_store.py`

- **class** `WGAuthUser` — line 13
  - **method** `def principal(self)` — line 19
- **class** `WGAuthUserStore` — line 23
  - **method** `def __init__(self, login_dir, opaque_record_len = 256)` — line 26
  - **method** `def _path(self, username)` — line 31
  - **method** `def load(self, username)` — line 45
  - **method** `def _write_user(self, user, *, replace = True)` — line 86
  - **method** `def add_peer(self, username, public_key)` — line 122
  - **method** `def remove_peer(self, username, public_key)` — line 141
  - **method** `def create_user(self, username, credential_record)` — line 164
  - **method** `def delete_user(self, username)` — line 181
  - **method** `def list_users(self)` — line 193
  - **method** `def peer_owners(self)` — line 209

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client.py`

- **variable** `log` — line 24
- **function** `def setup_logging()` — line 27
- **function** `def systemd_notify(message)` — line 36
- **function** `def _manager_peer_snapshot(api)` — line 55
- **function** `def activate(ipc, lifecycle)` — line 97
- **function** `def main()` — line 187

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_API.py`

- **variable** `log` — line 13
- **class** `WGClientAPI` — line 17
  - **method** `def __init__(self, config, listen_path, session, lifecycle = None)` — line 18
  - **method** `def start(self)` — line 74
  - **method** `def bind(self)` — line 79
  - **method** `def serve(self)` — line 119
  - **method** `def stop(self)` — line 132
  - **method** `def close(self)` — line 146

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_API_handler.py`

- **variable** `log` — line 23
- **variable** `MAX_BODY_SIZE` — line 26
- **variable** `PEERS_PREFIX` — line 28
- **variable** `ADMIN_PEERS_PATH` — line 29
- **variable** `ADMIN_PEERS_PREFIX` — line 30
- **variable** `ADMIN_USERS_PATH` — line 31
- **variable** `ADMIN_USERS_PREFIX` — line 32
- **variable** `SESSION_PATH` — line 33
- **variable** `HEARTBEAT_PATH` — line 34
- **variable** `PROVISIONING_PATH` — line 35
- **variable** `AUTH_SESSION_ID_HEADER` — line 40
- **variable** `AUTH_COUNTER_HEADER` — line 41
- **variable** `AUTH_NONCE_HEADER` — line 42
- **variable** `AUTH_MAC_HEADER` — line 43
- **variable** `_AUTH_MALFORMED_ERRORS` — line 48
- **variable** `_AUTH_REJECTED_ERRORS` — line 56
- **class** `WGClientHTTPServer` (http.server.ThreadingHTTPServer) — line 65
  - **method** `def __init__(self, server_address, handler_class, peer_service, listen_path, session, lifecycle)` — line 66
- **class** `WGClientAPIHandler` (http.server.BaseHTTPRequestHandler) — line 93
  - **method** `def handle_one_request(self)` — line 103
  - **method** `def peer_service(self)` — line 114
  - **method** `def session(self)` — line 121
  - **method** `def session_lock(self)` — line 128
  - **method** `def api_path(self)` — line 131
  - **method** `def _decode_peer_component(value)` — line 149
  - **method** `def api_target(self)` — line 161
  - **method** `def peer_key(self, path)` — line 210
  - **method** `def admin_owner_key(self, path)` — line 221
  - **method** `def log_message(self, format, *args)` — line 236
  - **method** `def request_auth_headers(self)` — line 243
  - **method** `def authenticate_request(self, body)` — line 272
  - **method** `def _authenticated_headers(self, code, body)` — line 318
  - **method** `def send_error(self, code, message = None, explain = None)` — line 346
  - **method** `def send_json(self, code, obj)` — line 406
  - **method** `def do_GET(self)` — line 440
  - **method** `def do_POST(self)` — line 481
  - **method** `def do_DELETE(self)` — line 538
  - **method** `def do_CONNECT(self)` — line 588
  - **method** `def do_PATCH(self)` — line 592
  - **method** `def do_PUT(self)` — line 596

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_IPC.py`

- **variable** `log` — line 9
- **variable** `MAX_PACKET_SIZE` — line 11
- **variable** `PROTOCOL_VERSION` — line 13
- **variable** `OPAQUE_SESSION_KEY_SIZE` — line 16
- **variable** `MAX_SESSION_TIMEOUT` — line 19
- **variable** `MAX_CLOCK_SKEW` — line 22
- **variable** `LISTEN_PATH_RE` — line 24
- **variable** `IPC_RESPONSE_TIMEOUT` — line 25
- **class** `WGClientIPC` — line 28
  - **method** `def __init__(self, sock, lifecycle)` — line 30
  - **method** `def control_loop(self)` — line 41
  - **method** `def receive_packet(self)` — line 94
  - **method** `def parse_packet(self, packet)` — line 122
  - **method** `def _int_field(self, obj, name)` — line 142
  - **method** `def _hex_field(self, obj, name)` — line 152
  - **method** `def parse_activation(self, obj, now = None)` — line 164
  - **method** `def _complete_pending(self, response)` — line 247
  - **method** `def _fail_pending(self, error)` — line 262
  - **method** `def _peer_request(self, command, public_key, allowed_ip = None)` — line 270
  - **method** `def register_peer(self, public_key, allowed_ip)` — line 350
  - **method** `def unregister_peer(self, public_key)` — line 357
  - **method** `def _ownership_request(self, command, **fields)` — line 360
  - **method** `def provisioning_state(self)` — line 428
  - **method** `def ownership_state(self)` — line 478
  - **method** `def reassign_owner(self, public_key, username)` — line 481
  - **method** `def _account_request(self, command, **fields)` — line 493
  - **method** `def create_user(self, username, password)` — line 559
  - **method** `def delete_user(self, username)` — line 566
  - **method** `def reconcile_state(self, peers)` — line 572
  - **method** `def _encode_packet(self, packet)` — line 605
  - **method** `def send_result(self, status, **fields)` — line 617
  - **method** `def keepalive(self)` — line 631
  - **method** `def _notify_stop(self)` — line 649
  - **method** `def stop(self, notify_shutdown = True)` — line 660

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_activator.py`

- **class** `WGClientActivation` — line 5
  - **method** `def __init__(self, sock, response)` — line 6
  - **method** `def close(self)` — line 10
  - **method** `def __enter__(self)` — line 15
  - **method** `def __exit__(self, exc_type, exc_value, traceback)` — line 18
- **function** `def activate_client(socket_path, k_sess, timeout, client_id, session_id, listen_path, principal, state_reconcile = None)` — line 21

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_config.py`

- **variable** `DEFAULT_CONFIG` — line 8
- **variable** `DEFAULT_SECURE_SESSION_ENABLED` — line 11
- **variable** `DEFAULT_SESSION_ID_SIZE` — line 12
- **variable** `DEFAULT_NONCE_SIZE` — line 13
- **variable** `DEFAULT_SESSION_KEY_SIZE` — line 14
- **variable** `DEFAULT_COUNTER_MIN` — line 15
- **variable** `DEFAULT_COUNTER_MAX` — line 16
- **variable** `DEFAULT_SESSION_TIMEOUT` — line 17
- **variable** `DEFAULT_MAX_REQUEST_FREQUENCY` — line 20
- **variable** `DEFAULT_REPLAY_WINDOW_SIZE` — line 21
- **function** `def load_config()` — line 24

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_errors.py`

- **class** `WGError` (Exception) — line 1
- **class** `WGControllerError` (WGError) — line 7
  - **method** `def __init__(self, status, message, response = None)` — line 10
- **class** `WGClientError` (WGError) — line 18
- **class** `WGPeerError` (WGClientError) — line 24
  - **method** `def __init__(self, status, message)` — line 27
- **class** `WGAuthenticationError` (WGClientError) — line 33
- **class** `WGSessionError` (WGClientError) — line 39
- **class** `WGProtocolError` (WGClientError) — line 45
- **class** `WGConnectionClosed` (WGProtocolError) — line 51
- **class** `WGPeerPersistenceError` (WGProtocolError) — line 57
  - **method** `def __init__(self, status, message)` — line 60
- **class** `WGAPIError` (WGClientError) — line 66
- **class** `WGReplayError` (WGProtocolError) — line 72
- **class** `WGMalformedMessageError` (WGProtocolError) — line 76
- **class** `WGInvalidFieldError` (WGProtocolError) — line 81
- **class** `WGInvalidEncodingError` (WGProtocolError) — line 86
- **class** `WGCounterError` (WGProtocolError) — line 91
- **class** `WGCounterExhaustedError` (WGCounterError) — line 96
- **class** `WGSessionExpiredError` (WGSessionError) — line 101
- **class** `WGRequestRateExceededError` (WGSessionError) — line 106
- **class** `WGInvalidMACError` (WGAuthenticationError) — line 111
- **class** `WGSessionMismatchError` (WGAuthenticationError) — line 116

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_lifecycle.py`

- **variable** `log` — line 4
- **class** `WGClientLifecycle` — line 5
  - **method** `def __init__(self, api = None, ipc = None)` — line 6
  - **method** `def notify_activity(self)` — line 13
  - **method** `def request_shutdown(self, notify_shutdown = True)` — line 20

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_controller_client.py`

- **class** `WGControllerClient` — line 13
  - **method** `def __init__(self, host, port, ca, cert, key, timeout = 10)` — line 14
  - **method** `def _request(self, method, path, body = None)` — line 24
  - **method** `def status(self)` — line 76
  - **method** `def provisioning(self)` — line 81
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 85
  - **method** `def remove_peer(self, public_key)` — line 97
- **class** `WGClientClient` — line 105
  - **method** `def __init__(self, host, port, ca, cert, key, timeout = 10, listen_path = None, secure_session = None)` — line 106
  - **method** `def _request(self, method, path, body = None)` — line 122
  - **method** `def status(self)` — line 197
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 202
  - **method** `def remove_peer(self, public_key)` — line 214

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_peer_service.py`

- **variable** `log` — line 13
- **class** `WGPeerService` — line 16
  - **method** `def __init__(self, controller, session, lifecycle, interface, endpoint = None)` — line 19
  - **method** `def ipc(self)` — line 33
  - **method** `def _controller_status(self)` — line 42
  - **method** `def status(self)` — line 59
  - **method** `def provisioning(self)` — line 83
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 131
  - **method** `def remove_peer(self, public_key)` — line 194
  - **method** `def admin_status(self)` — line 225
  - **method** `def reassign_owner(self, public_key, username)` — line 262
  - **method** `def create_user(self, username, password)` — line 277
  - **method** `def delete_user(self, username)` — line 288

## `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_secure_session.py`

- **variable** `log` — line 29
- **class** `WGSecureSession` — line 32
  - **method** `def __init__(self, config, k_session: bytes, session_id: bytes | None = None, principal = None, rng = None, clock = None)` — line 56
  - **method** `def session_id(self) -> bytes` — line 191
  - **method** `def session_id_b64(self) -> str` — line 196
  - **method** `def principal(self)` — line 201
  - **method** `def is_admin(self)` — line 205
  - **method** `def can_access_peer(self, public_key)` — line 211
  - **method** `def register_peer(self, public_key)` — line 220
  - **method** `def unregister_peer(self, public_key)` — line 229
  - **method** `def _derive_session_seed(self) -> bytes` — line 243
  - **method** `def _derive_key(self, purpose: bytes) -> bytes` — line 252
  - **method** `def create_request_auth(self, method: str, path: str, body: bytes = b'') -> dict` — line 265
  - **method** `def _create_request_auth_unlocked(self, method: str, path: str, body: bytes = b'') -> dict` — line 279
  - **method** `def create_response_auth(self, request_auth: dict, status: int, body: bytes = b'') -> dict` — line 342
  - **method** `def _create_response_auth_unlocked(self, request_auth: dict, status: int, body: bytes = b'') -> dict` — line 356
  - **method** `def verify_request(self, auth: dict, method: str, path: str, body: bytes = b'') -> bool` — line 409
  - **method** `def _verify_request_unlocked(self, auth: dict, method: str, path: str, body: bytes = b'') -> bool` — line 425
  - **method** `def verify_response(self, auth: dict, request_auth: dict, status: int, body: bytes = b'') -> bool` — line 504
  - **method** `def _verify_response_unlocked(self, auth: dict, request_auth: dict, status: int, body: bytes = b'') -> bool` — line 521
  - **method** `def _check_session_active_unlocked(self)` — line 615
  - **method** `def _check_request_rate_unlocked(self)` — line 620
  - **method** `def _counter_in_receive_window_unlocked(self, counter, highest_seen)` — line 634
  - **method** `def _accept_receive_counter_unlocked(self, counter, request)` — line 641
  - **method** `def _validate_auth_structure(auth: dict, required_fields: tuple) -> None` — line 669
  - **method** `def _validate_session_id(self, value) -> bytes` — line 679
  - **method** `def _validate_counter(self, value) -> int` — line 689
  - **method** `def _validate_nonce(self, value) -> bytes` — line 698
  - **method** `def _validate_mac(self, value) -> bytes` — line 708
  - **method** `def _validate_request_auth(self, auth: dict) -> dict` — line 718
  - **method** `def _validate_response_auth(self, auth: dict) -> dict` — line 732
  - **method** `def _request_message(self, counter: int, nonce: bytes, method: str, path: str, body: bytes) -> bytes` — line 755
  - **method** `def _response_message(self, counter: int, nonce: bytes, status: int, body: bytes) -> bytes` — line 778
  - **method** `def _b64(value: bytes) -> str` — line 804
  - **method** `def _unb64(value: str) -> bytes` — line 809

## `debian/wg-manager-auth-client/usr/share/wg-manager/frontend/app.js`

- **function** `setConfigPendingExport` — line 42
- **function** `confirmDiscardPendingConfig` — line 46
- **function** `stopHeartbeat` — line 84
- **function** `startHeartbeat` — line 91
- **function** `showAuthView` — line 126
- **function** `showPeerView` — line 132
- **function** `showPostauthView` — line 138
- **function** `renderPeers` — line 147
- **function** `clientAllowedIpsForMode` — line 373
- **function** `base64UrlToWireGuard` — line 383
- **function** `generateWireGuardKeyPair` — line 391
- **function** `configIsComplete` — line 418
- **function** `updateQrAvailability` — line 427
- **function** `renderClientConfigPreview` — line 443
- **function** `refreshProvisioning` — line 477
- **function** `refreshPeers` — line 538
- **function** `renderAdminState` — line 559
- **function** `refreshAdmin` — line 689
- **function** `refreshAuthStatus` — line 709
- **function** `renderQrCode` — line 986

## `debian/wg-manager-auth-client/usr/share/wg-manager/js/wg_auth_session.js`

- **class** `WGAuthSession` — line 2

## `debian/wg-manager-auth-client/usr/share/wg-manager/js/wg_client_api.js`

- **class** `WGClientAPI` — line 17

## `debian/wg-manager-auth-client/usr/share/wg-manager/js/wg_client_errors.js`

- **class** `WGError` (Error) — line 18
- **class** `WGClientError` (WGError) — line 25
- **class** `WGProtocolError` (WGClientError) — line 32
- **class** `WGMalformedMessageError` (WGProtocolError) — line 39
- **class** `WGInvalidFieldError` (WGProtocolError) — line 46
- **class** `WGInvalidEncodingError` (WGProtocolError) — line 53
- **class** `WGCounterError` (WGProtocolError) — line 60
- **class** `WGCounterExhaustedError` (WGCounterError) — line 67
- **class** `WGAuthenticationError` (WGClientError) — line 74
- **class** `WGInvalidMACError` (WGAuthenticationError) — line 81
- **class** `WGSessionMismatchError` (WGAuthenticationError) — line 88
- **class** `WGSessionError` (WGClientError) — line 95
- **class** `WGSessionExpiredError` (WGSessionError) — line 102
- **class** `WGRequestRateExceededError` (WGSessionError) — line 109
- **class** `WGReplayError` (WGProtocolError) — line 116

## `debian/wg-manager-auth-client/usr/share/wg-manager/js/wg_opaque_client.js`

- **function** `opaqueLibrary` — line 1
- **class** `WGOPAQUEClient` — line 12

## `debian/wg-manager-auth-client/usr/share/wg-manager/js/wg_secure_session.js`

- **function** `getSubtle` — line 57
- **function** `getRandomBytes` — line 64
- **function** `concatBytes` — line 77
- **function** `bytesToHex` — line 88
- **function** `hexToBytes` — line 94
- **function** `b64encode` — line 107
- **function** `b64decode` — line 115
- **function** `sha256` — line 136
- **class** `WGSecureSession` — line 152
- **function** `bytesEqual` — line 679

## `debian/wg-manager-controller/usr/lib/wg-manager/src/wg_manager/wg_manager.py`

- **variable** `CONFIG` — line 6
- **variable** `WG_PROGRAM` — line 7
- **function** `def log(msg)` — line 13
- **class** `E` (Exception) — line 17
  - **method** `def __init__(self, code, msg)` — line 18
- **function** `def cfg()` — line 22
- **function** `def reply(s, code, obj)` — line 36
- **function** `def request(s)` — line 44
- **function** `def wg(args)` — line 79
- **function** `def key(k)` — line 94
- **function** `def peers(interface)` — line 104
- **function** `def provisioning(c)` — line 123
- **function** `def add(c, o)` — line 160
- **function** `def remove(c, pk)` — line 180
- **function** `def dispatch(c, m, t, b)` — line 188
- **function** `def systemd_socket()` — line 205
- **function** `def tls(c)` — line 218
- **function** `def main()` — line 231

## `src/wg_auth/wg_auth.py`

- **variable** `log` — line 12
- **variable** `config_path` — line 13
- **function** `def load_config(path)` — line 18
- **function** `def main()` — line 24

## `src/wg_auth/wg_auth_API.py`

- **variable** `log` — line 14
- **class** `WGAuthAPI` — line 17
  - **method** `def __init__(self, config, lifecycle)` — line 23
  - **method** `def __enter__(self)` — line 57
  - **method** `def __exit__(self, exc_type, exc_value, traceback)` — line 61
  - **method** `def run(self)` — line 64
  - **method** `def stop(self)` — line 70
  - **method** `def get_session_status(self)` — line 80
  - **method** `def start_authentication(self, username, pubU)` — line 97
  - **method** `def finish_authentication(self, authU)` — line 135
  - **method** `def _register_peer(self, username, public_key, allowed_ip)` — line 232
  - **method** `def _unregister_peer(self, username, public_key)` — line 245
  - **method** `def _reconcile_peer_state(self, manager_peers)` — line 260
  - **method** `def _provisioning_state(self)` — line 267
  - **method** `def _ownership_state(self)` — line 274
  - **method** `def _reassign_ownership(self, public_key, username)` — line 277
  - **method** `def _create_account(self, username, password)` — line 283
  - **method** `def _delete_account(self, username)` — line 289
  - **method** `def _activation_failed(self, session, ipc)` — line 298
  - **method** `def logout(self, notify_client = True)` — line 321
  - **method** `def _finish_shutdown(self, session, ipc, notify_client = True)` — line 366
  - **method** `def _create_server(self)` — line 397

## `src/wg_auth/wg_auth_API_handler.py`

- **variable** `log` — line 9
- **class** `WGAuthAPIHandler` (BaseHTTPRequestHandler) — line 11
  - **method** `def _send_json(self, status, payload)` — line 14
  - **method** `def _read_json(self)` — line 26
  - **method** `def _handle_auth_start(self)` — line 46
  - **method** `def _handle_auth_verify(self)` — line 118
  - **method** `def do_POST(self)` — line 188
  - **method** `def do_DELETE(self)` — line 202
  - **method** `def do_GET(self)` — line 221

## `src/wg_auth/wg_auth_IPC.py`

- **variable** `log` — line 8
- **variable** `MAX_PACKET_SIZE` — line 11
- **variable** `PROTOCOL_VERSION` — line 12
- **class** `WGAuthIPC` — line 15
  - **method** `def __init__(self, socket_path, client_id, timeout, listen_path, lifecycle, principal = None, peer_register = None, peer_unregister = None, state_reconcile = None, provisioning_state = None, ownership_state = None, ownership_reassign = None, account_create = None, account_delete = None)` — line 17
  - **method** `def active(self)` — line 52
  - **method** `def control_loop(self)` — line 55
  - **method** `def _handle_peer_request(self, request)` — line 142
  - **method** `def _handle_provisioning_request(self, request)` — line 215
  - **method** `def _handle_ownership_request(self, request)` — line 245
  - **method** `def _handle_account_request(self, request)` — line 332
  - **method** `def receive_packet(self)` — line 426
  - **method** `def parse_packet(self, packet)` — line 461
  - **method** `def activate(self, session_id, k_session)` — line 488
  - **method** `def deactivate(self)` — line 556
  - **method** `def _encode_packet(self, packet)` — line 567
  - **method** `def send_packet(self, packet)` — line 580
  - **method** `def close(self)` — line 583

## `src/wg_auth/wg_auth_account_service.py`

- **variable** `SERVER_ID` — line 6
- **class** `WGAuthAccountService` — line 9
  - **method** `def __init__(self, user_store)` — line 12
  - **method** `def make_opaque_record(username, password)` — line 16
  - **method** `def create(self, username, password)` — line 45
  - **method** `def delete(self, username)` — line 59

## `src/wg_auth/wg_auth_errors.py`

- **class** `WGAuthError` (Exception) — line 1
  - **method** `def __init__(self, message)` — line 3
- **class** `WGAuthSessionError` (WGAuthError) — line 8
- **class** `WGAuthAuthenticationError` (WGAuthError) — line 12
- **class** `WGAuthProtocolError` (WGAuthError) — line 16

## `src/wg_auth/wg_auth_lifecycle.py`

- **variable** `log` — line 4
- **class** `WGAuthLifecycle` — line 7
  - **method** `def __init__(self, api = None, ipc = None, idle_timeout = 45)` — line 9
  - **method** `def _cancel_idle_timer_locked(self)` — line 20
  - **method** `def _arm_idle_timer_locked(self)` — line 27
  - **method** `def _idle_timeout_expired(self)` — line 41
  - **method** `def touch_session(self)` — line 45
  - **method** `def request_shutdown(self)` — line 54
  - **method** `def request_session_shutdown(self, notify_client = True)` — line 70
  - **method** `def request_session_start(self)` — line 83

## `src/wg_auth/wg_auth_ownership_service.py`

- **class** `WGAuthOwnershipService` — line 3
  - **method** `def __init__(self, user_store, peer_registry)` — line 6
  - **method** `def admin_state(self)` — line 10
  - **method** `def reassign(self, public_key, target_username)` — line 40

## `src/wg_auth/wg_auth_peer_registry.py`

- **class** `WGAuthPeerRegistry` — line 9
  - **method** `def __init__(self, path, ip_path = None)` — line 12
  - **method** `def _load(self)` — line 24
  - **method** `def _write(self, obj)` — line 71
  - **method** `def _load_ips(self)` — line 78
  - **method** `def _write_path(self, path, obj, prefix)` — line 120
  - **method** `def _write_registries(self, peers_obj, ips_obj)` — line 146
  - **method** `def reserve(self, username, public_key, allowed_ip)` — line 158
  - **method** `def release(self, actor_username, public_key)` — line 199
  - **method** `def get(self, public_key)` — line 226
  - **method** `def snapshot(self)` — line 231
  - **method** `def snapshot_ips(self)` — line 238
  - **method** `def set_owner(self, public_key, username)` — line 245
  - **method** `def reconcile(self, manager_peers, owners)` — line 270

## `src/wg_auth/wg_auth_session.py`

- **variable** `log` — line 13
- **variable** `OPAQUE_SESSION_KEY_SIZE` — line 17
- **class** `WGAuthSession` — line 20
  - **method** `def __init__(self, username, credential_record, context, principal = None)` — line 26
  - **method** `def authenticated(self)` — line 41
  - **method** `def session_id(self)` — line 45
  - **method** `def k_session(self)` — line 54
  - **method** `def create_credential_response(self, pubU)` — line 66
  - **method** `def authenticate(self, authU)` — line 126
  - **method** `def logout(self)` — line 166

## `src/wg_auth/wg_auth_user_store.py`

- **class** `WGAuthUser` — line 13
  - **method** `def principal(self)` — line 19
- **class** `WGAuthUserStore` — line 23
  - **method** `def __init__(self, login_dir, opaque_record_len = 256)` — line 26
  - **method** `def _path(self, username)` — line 31
  - **method** `def load(self, username)` — line 45
  - **method** `def _write_user(self, user, *, replace = True)` — line 86
  - **method** `def add_peer(self, username, public_key)` — line 122
  - **method** `def remove_peer(self, username, public_key)` — line 141
  - **method** `def create_user(self, username, credential_record)` — line 164
  - **method** `def delete_user(self, username)` — line 181
  - **method** `def list_users(self)` — line 193
  - **method** `def peer_owners(self)` — line 209

## `src/wg_client/wg_client.py`

- **variable** `log` — line 24
- **function** `def setup_logging()` — line 27
- **function** `def systemd_notify(message)` — line 36
- **function** `def _manager_peer_snapshot(api)` — line 55
- **function** `def activate(ipc, lifecycle)` — line 97
- **function** `def main()` — line 187

## `src/wg_client/wg_client_API.py`

- **variable** `log` — line 13
- **class** `WGClientAPI` — line 17
  - **method** `def __init__(self, config, listen_path, session, lifecycle = None)` — line 18
  - **method** `def start(self)` — line 74
  - **method** `def bind(self)` — line 79
  - **method** `def serve(self)` — line 119
  - **method** `def stop(self)` — line 132
  - **method** `def close(self)` — line 146

## `src/wg_client/wg_client_API_handler.py`

- **variable** `log` — line 23
- **variable** `MAX_BODY_SIZE` — line 26
- **variable** `PEERS_PREFIX` — line 28
- **variable** `ADMIN_PEERS_PATH` — line 29
- **variable** `ADMIN_PEERS_PREFIX` — line 30
- **variable** `ADMIN_USERS_PATH` — line 31
- **variable** `ADMIN_USERS_PREFIX` — line 32
- **variable** `SESSION_PATH` — line 33
- **variable** `HEARTBEAT_PATH` — line 34
- **variable** `PROVISIONING_PATH` — line 35
- **variable** `AUTH_SESSION_ID_HEADER` — line 40
- **variable** `AUTH_COUNTER_HEADER` — line 41
- **variable** `AUTH_NONCE_HEADER` — line 42
- **variable** `AUTH_MAC_HEADER` — line 43
- **variable** `_AUTH_MALFORMED_ERRORS` — line 48
- **variable** `_AUTH_REJECTED_ERRORS` — line 56
- **class** `WGClientHTTPServer` (http.server.ThreadingHTTPServer) — line 65
  - **method** `def __init__(self, server_address, handler_class, peer_service, listen_path, session, lifecycle)` — line 66
- **class** `WGClientAPIHandler` (http.server.BaseHTTPRequestHandler) — line 93
  - **method** `def handle_one_request(self)` — line 103
  - **method** `def peer_service(self)` — line 114
  - **method** `def session(self)` — line 121
  - **method** `def session_lock(self)` — line 128
  - **method** `def api_path(self)` — line 131
  - **method** `def _decode_peer_component(value)` — line 149
  - **method** `def api_target(self)` — line 161
  - **method** `def peer_key(self, path)` — line 210
  - **method** `def admin_owner_key(self, path)` — line 221
  - **method** `def log_message(self, format, *args)` — line 236
  - **method** `def request_auth_headers(self)` — line 243
  - **method** `def authenticate_request(self, body)` — line 272
  - **method** `def _authenticated_headers(self, code, body)` — line 318
  - **method** `def send_error(self, code, message = None, explain = None)` — line 346
  - **method** `def send_json(self, code, obj)` — line 406
  - **method** `def do_GET(self)` — line 440
  - **method** `def do_POST(self)` — line 481
  - **method** `def do_DELETE(self)` — line 538
  - **method** `def do_CONNECT(self)` — line 588
  - **method** `def do_PATCH(self)` — line 592
  - **method** `def do_PUT(self)` — line 596

## `src/wg_client/wg_client_IPC.py`

- **variable** `log` — line 9
- **variable** `MAX_PACKET_SIZE` — line 11
- **variable** `PROTOCOL_VERSION` — line 13
- **variable** `OPAQUE_SESSION_KEY_SIZE` — line 16
- **variable** `MAX_SESSION_TIMEOUT` — line 19
- **variable** `MAX_CLOCK_SKEW` — line 22
- **variable** `LISTEN_PATH_RE` — line 24
- **variable** `IPC_RESPONSE_TIMEOUT` — line 25
- **class** `WGClientIPC` — line 28
  - **method** `def __init__(self, sock, lifecycle)` — line 30
  - **method** `def control_loop(self)` — line 41
  - **method** `def receive_packet(self)` — line 94
  - **method** `def parse_packet(self, packet)` — line 122
  - **method** `def _int_field(self, obj, name)` — line 142
  - **method** `def _hex_field(self, obj, name)` — line 152
  - **method** `def parse_activation(self, obj, now = None)` — line 164
  - **method** `def _complete_pending(self, response)` — line 247
  - **method** `def _fail_pending(self, error)` — line 262
  - **method** `def _peer_request(self, command, public_key, allowed_ip = None)` — line 270
  - **method** `def register_peer(self, public_key, allowed_ip)` — line 350
  - **method** `def unregister_peer(self, public_key)` — line 357
  - **method** `def _ownership_request(self, command, **fields)` — line 360
  - **method** `def provisioning_state(self)` — line 428
  - **method** `def ownership_state(self)` — line 478
  - **method** `def reassign_owner(self, public_key, username)` — line 481
  - **method** `def _account_request(self, command, **fields)` — line 493
  - **method** `def create_user(self, username, password)` — line 559
  - **method** `def delete_user(self, username)` — line 566
  - **method** `def reconcile_state(self, peers)` — line 572
  - **method** `def _encode_packet(self, packet)` — line 605
  - **method** `def send_result(self, status, **fields)` — line 617
  - **method** `def keepalive(self)` — line 631
  - **method** `def _notify_stop(self)` — line 649
  - **method** `def stop(self, notify_shutdown = True)` — line 660

## `src/wg_client/wg_client_activator.py`

- **class** `WGClientActivation` — line 5
  - **method** `def __init__(self, sock, response)` — line 6
  - **method** `def close(self)` — line 10
  - **method** `def __enter__(self)` — line 15
  - **method** `def __exit__(self, exc_type, exc_value, traceback)` — line 18
- **function** `def activate_client(socket_path, k_sess, timeout, client_id, session_id, listen_path, principal, state_reconcile = None)` — line 21

## `src/wg_client/wg_client_config.py`

- **variable** `DEFAULT_CONFIG` — line 8
- **variable** `DEFAULT_SECURE_SESSION_ENABLED` — line 11
- **variable** `DEFAULT_SESSION_ID_SIZE` — line 12
- **variable** `DEFAULT_NONCE_SIZE` — line 13
- **variable** `DEFAULT_SESSION_KEY_SIZE` — line 14
- **variable** `DEFAULT_COUNTER_MIN` — line 15
- **variable** `DEFAULT_COUNTER_MAX` — line 16
- **variable** `DEFAULT_SESSION_TIMEOUT` — line 17
- **variable** `DEFAULT_MAX_REQUEST_FREQUENCY` — line 20
- **variable** `DEFAULT_REPLAY_WINDOW_SIZE` — line 21
- **function** `def load_config()` — line 24

## `src/wg_client/wg_client_errors.js`

- **class** `WGError` (Error) — line 18
- **class** `WGProtocolError` (WGError) — line 25
- **class** `WGMalformedMessageError` (WGProtocolError) — line 32
- **class** `WGInvalidFieldError` (WGProtocolError) — line 39
- **class** `WGInvalidEncodingError` (WGProtocolError) — line 46
- **class** `WGCounterError` (WGProtocolError) — line 53
- **class** `WGCounterExhaustedError` (WGCounterError) — line 60
- **class** `WGAuthenticationError` (WGError) — line 67
- **class** `WGInvalidMACError` (WGAuthenticationError) — line 74
- **class** `WGSessionMismatchError` (WGAuthenticationError) — line 81
- **class** `WGReplayError` (WGError) — line 88
- **class** `WGSessionExpiredError` (WGError) — line 95
- **class** `WGRequestRateExceededError` (WGError) — line 101

## `src/wg_client/wg_client_errors.py`

- **class** `WGError` (Exception) — line 1
- **class** `WGControllerError` (WGError) — line 7
  - **method** `def __init__(self, status, message, response = None)` — line 10
- **class** `WGClientError` (WGError) — line 18
- **class** `WGPeerError` (WGClientError) — line 24
  - **method** `def __init__(self, status, message)` — line 27
- **class** `WGAuthenticationError` (WGClientError) — line 33
- **class** `WGSessionError` (WGClientError) — line 39
- **class** `WGProtocolError` (WGClientError) — line 45
- **class** `WGConnectionClosed` (WGProtocolError) — line 51
- **class** `WGPeerPersistenceError` (WGProtocolError) — line 57
  - **method** `def __init__(self, status, message)` — line 60
- **class** `WGAPIError` (WGClientError) — line 66
- **class** `WGReplayError` (WGProtocolError) — line 72
- **class** `WGMalformedMessageError` (WGProtocolError) — line 76
- **class** `WGInvalidFieldError` (WGProtocolError) — line 81
- **class** `WGInvalidEncodingError` (WGProtocolError) — line 86
- **class** `WGCounterError` (WGProtocolError) — line 91
- **class** `WGCounterExhaustedError` (WGCounterError) — line 96
- **class** `WGSessionExpiredError` (WGSessionError) — line 101
- **class** `WGRequestRateExceededError` (WGSessionError) — line 106
- **class** `WGInvalidMACError` (WGAuthenticationError) — line 111
- **class** `WGSessionMismatchError` (WGAuthenticationError) — line 116

## `src/wg_client/wg_client_lifecycle.py`

- **variable** `log` — line 4
- **class** `WGClientLifecycle` — line 5
  - **method** `def __init__(self, api = None, ipc = None)` — line 6
  - **method** `def notify_activity(self)` — line 13
  - **method** `def request_shutdown(self, notify_shutdown = True)` — line 20

## `src/wg_client/wg_controller_client.py`

- **class** `WGControllerClient` — line 13
  - **method** `def __init__(self, host, port, ca, cert, key, timeout = 10)` — line 14
  - **method** `def _request(self, method, path, body = None)` — line 24
  - **method** `def status(self)` — line 76
  - **method** `def provisioning(self)` — line 81
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 85
  - **method** `def remove_peer(self, public_key)` — line 97
- **class** `WGClientClient` — line 105
  - **method** `def __init__(self, host, port, ca, cert, key, timeout = 10, listen_path = None, secure_session = None)` — line 106
  - **method** `def _request(self, method, path, body = None)` — line 122
  - **method** `def status(self)` — line 197
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 202
  - **method** `def remove_peer(self, public_key)` — line 214

## `src/wg_client/wg_peer_service.py`

- **variable** `log` — line 13
- **class** `WGPeerService` — line 16
  - **method** `def __init__(self, controller, session, lifecycle, interface, endpoint = None)` — line 19
  - **method** `def ipc(self)` — line 33
  - **method** `def _controller_status(self)` — line 42
  - **method** `def status(self)` — line 59
  - **method** `def provisioning(self)` — line 83
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 131
  - **method** `def remove_peer(self, public_key)` — line 194
  - **method** `def admin_status(self)` — line 225
  - **method** `def reassign_owner(self, public_key, username)` — line 262
  - **method** `def create_user(self, username, password)` — line 277
  - **method** `def delete_user(self, username)` — line 288

## `src/wg_client/wg_secure_session.py`

- **variable** `log` — line 29
- **class** `WGSecureSession` — line 32
  - **method** `def __init__(self, config, k_session: bytes, session_id: bytes | None = None, principal = None, rng = None, clock = None)` — line 56
  - **method** `def session_id(self) -> bytes` — line 191
  - **method** `def session_id_b64(self) -> str` — line 196
  - **method** `def principal(self)` — line 201
  - **method** `def is_admin(self)` — line 205
  - **method** `def can_access_peer(self, public_key)` — line 211
  - **method** `def register_peer(self, public_key)` — line 220
  - **method** `def unregister_peer(self, public_key)` — line 229
  - **method** `def _derive_session_seed(self) -> bytes` — line 243
  - **method** `def _derive_key(self, purpose: bytes) -> bytes` — line 252
  - **method** `def create_request_auth(self, method: str, path: str, body: bytes = b'') -> dict` — line 265
  - **method** `def _create_request_auth_unlocked(self, method: str, path: str, body: bytes = b'') -> dict` — line 279
  - **method** `def create_response_auth(self, request_auth: dict, status: int, body: bytes = b'') -> dict` — line 342
  - **method** `def _create_response_auth_unlocked(self, request_auth: dict, status: int, body: bytes = b'') -> dict` — line 356
  - **method** `def verify_request(self, auth: dict, method: str, path: str, body: bytes = b'') -> bool` — line 409
  - **method** `def _verify_request_unlocked(self, auth: dict, method: str, path: str, body: bytes = b'') -> bool` — line 425
  - **method** `def verify_response(self, auth: dict, request_auth: dict, status: int, body: bytes = b'') -> bool` — line 504
  - **method** `def _verify_response_unlocked(self, auth: dict, request_auth: dict, status: int, body: bytes = b'') -> bool` — line 521
  - **method** `def _check_session_active_unlocked(self)` — line 615
  - **method** `def _check_request_rate_unlocked(self)` — line 620
  - **method** `def _counter_in_receive_window_unlocked(self, counter, highest_seen)` — line 634
  - **method** `def _accept_receive_counter_unlocked(self, counter, request)` — line 641
  - **method** `def _validate_auth_structure(auth: dict, required_fields: tuple) -> None` — line 669
  - **method** `def _validate_session_id(self, value) -> bytes` — line 679
  - **method** `def _validate_counter(self, value) -> int` — line 689
  - **method** `def _validate_nonce(self, value) -> bytes` — line 698
  - **method** `def _validate_mac(self, value) -> bytes` — line 708
  - **method** `def _validate_request_auth(self, auth: dict) -> dict` — line 718
  - **method** `def _validate_response_auth(self, auth: dict) -> dict` — line 732
  - **method** `def _request_message(self, counter: int, nonce: bytes, method: str, path: str, body: bytes) -> bytes` — line 755
  - **method** `def _response_message(self, counter: int, nonce: bytes, status: int, body: bytes) -> bytes` — line 778
  - **method** `def _b64(value: bytes) -> str` — line 804
  - **method** `def _unb64(value: str) -> bytes` — line 809

## `src/wg_frontend/check_vectors.mjs`

- **function** `assertEqual` — line 30
- **function** `main` — line 42

## `src/wg_frontend/wg_auth_session.js`

- **class** `WGAuthSession` — line 2

## `src/wg_frontend/wg_client_api.js`

- **class** `WGClientAPI` — line 17

## `src/wg_frontend/wg_client_errors.js`

- **class** `WGError` (Error) — line 18
- **class** `WGClientError` (WGError) — line 25
- **class** `WGProtocolError` (WGClientError) — line 32
- **class** `WGMalformedMessageError` (WGProtocolError) — line 39
- **class** `WGInvalidFieldError` (WGProtocolError) — line 46
- **class** `WGInvalidEncodingError` (WGProtocolError) — line 53
- **class** `WGCounterError` (WGProtocolError) — line 60
- **class** `WGCounterExhaustedError` (WGCounterError) — line 67
- **class** `WGAuthenticationError` (WGClientError) — line 74
- **class** `WGInvalidMACError` (WGAuthenticationError) — line 81
- **class** `WGSessionMismatchError` (WGAuthenticationError) — line 88
- **class** `WGSessionError` (WGClientError) — line 95
- **class** `WGSessionExpiredError` (WGSessionError) — line 102
- **class** `WGRequestRateExceededError` (WGSessionError) — line 109
- **class** `WGReplayError` (WGProtocolError) — line 116

## `src/wg_frontend/wg_opaque_client.js`

- **function** `opaqueLibrary` — line 1
- **class** `WGOPAQUEClient` — line 12

## `src/wg_frontend/wg_secure_session.js`

- **function** `getSubtle` — line 57
- **function** `getRandomBytes` — line 64
- **function** `concatBytes` — line 77
- **function** `bytesToHex` — line 88
- **function** `hexToBytes` — line 94
- **function** `b64encode` — line 107
- **function** `b64decode` — line 115
- **function** `sha256` — line 136
- **class** `WGSecureSession` — line 152
- **function** `bytesEqual` — line 679

## `src/wg_frontend/www/vpn/app.js`

- **function** `setConfigPendingExport` — line 42
- **function** `confirmDiscardPendingConfig` — line 46
- **function** `stopHeartbeat` — line 84
- **function** `startHeartbeat` — line 91
- **function** `showAuthView` — line 126
- **function** `showPeerView` — line 132
- **function** `showPostauthView` — line 138
- **function** `renderPeers` — line 147
- **function** `clientAllowedIpsForMode` — line 373
- **function** `base64UrlToWireGuard` — line 383
- **function** `generateWireGuardKeyPair` — line 391
- **function** `configIsComplete` — line 418
- **function** `updateQrAvailability` — line 427
- **function** `renderClientConfigPreview` — line 443
- **function** `refreshProvisioning` — line 477
- **function** `refreshPeers` — line 538
- **function** `renderAdminState` — line 559
- **function** `refreshAdmin` — line 689
- **function** `refreshAuthStatus` — line 709
- **function** `renderQrCode` — line 986

## `src/wg_manager/wg_manager.py`

- **variable** `CONFIG` — line 6
- **variable** `WG_PROGRAM` — line 7
- **function** `def log(msg)` — line 13
- **class** `E` (Exception) — line 17
  - **method** `def __init__(self, code, msg)` — line 18
- **function** `def cfg()` — line 22
- **function** `def reply(s, code, obj)` — line 36
- **function** `def request(s)` — line 44
- **function** `def wg(args)` — line 79
- **function** `def key(k)` — line 94
- **function** `def peers(interface)` — line 104
- **function** `def provisioning(c)` — line 123
- **function** `def add(c, o)` — line 160
- **function** `def remove(c, pk)` — line 180
- **function** `def dispatch(c, m, t, b)` — line 188
- **function** `def systemd_socket()` — line 205
- **function** `def tls(c)` — line 218
- **function** `def main()` — line 231

## `tests/auth/js/client_cli.js`

- **function** `loadConfig` — line 7
- **function** `main` — line 46

## `tests/auth/js/opaque_client.js`

- **class** `OpaqueClient` — line 4

## `tests/auth/js/wg_auth_client.js`

- **class** `WGAuthHTTPClient` — line 7

## `tests/auth/test_account_service.py`

- **function** `def test_create_and_delete_account(tmp_path)` — line 10
- **function** `def test_create_account_rejects_empty_password(tmp_path)` — line 36

## `tests/auth/test_auth_api_state.py`

- **class** `Lifecycle` — line 9
  - **method** `def __init__(self)` — line 10
- **class** `FakeSession` — line 14
  - **method** `def __init__(self)` — line 15
  - **method** `def logout(self)` — line 18
- **class** `FakeIPC` — line 22
  - **method** `def __init__(self)` — line 23
  - **method** `def close(self)` — line 26
- **function** `def make_api(tmp_path)` — line 30
- **function** `def test_finish_authentication_requires_start(tmp_path)` — line 47
- **function** `def test_start_authentication_rejects_non_idle_state(tmp_path)` — line 57
- **function** `def test_activation_failure_returns_api_to_idle(tmp_path)` — line 68
- **function** `def test_logout_during_starting_defers_cleanup(tmp_path)` — line 90

## `tests/auth/test_ownership_service.py`

- **function** `def make_service(tmp_path)` — line 10
- **function** `def test_admin_state_reports_orphan_and_stale(tmp_path)` — line 18
- **function** `def test_reassign_claims_orphan_peer(tmp_path)` — line 48
- **function** `def test_reassign_moves_peer_between_users(tmp_path)` — line 73
- **function** `def test_reassign_rejects_missing_target_user(tmp_path)` — line 97
- **function** `def test_admin_state_exposes_ip_registry(tmp_path)` — line 116

## `tests/auth/test_peer_registry.py`

- **function** `def test_reserve_and_release_peer(tmp_path)` — line 10
- **function** `def test_duplicate_public_key_is_rejected(tmp_path)` — line 33
- **function** `def test_duplicate_allowed_ip_is_rejected(tmp_path)` — line 44
- **function** `def test_admin_can_release_foreign_reservation(tmp_path)` — line 55
- **function** `def test_non_owner_cannot_release_foreign_reservation(tmp_path)` — line 67
- **function** `def test_reconcile_rebuilds_registry_from_live_state(tmp_path)` — line 78
- **function** `def test_reconcile_keeps_live_peer_without_owner_as_orphan(tmp_path)` — line 119
- **function** `def test_set_owner_repairs_orphan(tmp_path)` — line 142
- **function** `def test_reserve_updates_ip_registry(tmp_path)` — line 163
- **function** `def test_reconcile_rebuilds_ip_registry(tmp_path)` — line 190
- **function** `def test_set_owner_updates_ip_registry(tmp_path)` — line 216

## `tests/auth/test_user_store.py`

- **function** `def make_user_file(tmp_path, username = 'alice')` — line 9
- **function** `def test_add_and_remove_peer_are_persistent(tmp_path)` — line 24
- **function** `def test_add_peer_is_idempotent(tmp_path)` — line 45
- **function** `def test_remove_missing_peer_is_idempotent(tmp_path)` — line 55
- **function** `def test_create_and_delete_user(tmp_path)` — line 65
- **function** `def test_create_user_is_exclusive(tmp_path)` — line 82
- **function** `def test_delete_user_with_owned_peers_is_rejected(tmp_path)` — line 92
- **function** `def test_peer_owners_builds_global_index(tmp_path)` — line 105
- **function** `def test_peer_owners_rejects_duplicate_ownership(tmp_path)` — line 118

## `tests/client/test_admin_ipc.py`

- **class** `AuthLifecycle` — line 10
  - **method** `def __init__(self)` — line 11
  - **method** `def request_session_shutdown(self, notify_client = True)` — line 14
  - **method** `def request_shutdown(self)` — line 17
- **class** `ClientLifecycle` — line 21
- **function** `def test_admin_ipc_round_trip_for_ownership_and_accounts()` — line 25
- **function** `def test_non_admin_account_ipc_is_rejected_with_403()` — line 131

## `tests/client/test_peer_service.py`

- **class** `FakeSession` — line 13
  - **method** `def __init__(self, username = 'alice', peers = (), admin = False)` — line 14
  - **method** `def can_access_peer(self, public_key)` — line 22
  - **method** `def register_peer(self, public_key)` — line 25
  - **method** `def unregister_peer(self, public_key)` — line 28
- **class** `FakeIPC` — line 32
  - **method** `def __init__(self)` — line 33
  - **method** `def register_peer(self, public_key, allowed_ip)` — line 40
  - **method** `def unregister_peer(self, public_key)` — line 43
  - **method** `def ownership_state(self)` — line 46
  - **method** `def reassign_owner(self, public_key, username)` — line 50
  - **method** `def create_user(self, username, password)` — line 57
  - **method** `def delete_user(self, username)` — line 61
- **class** `FakeLifecycle` — line 66
  - **method** `def __init__(self)` — line 67
- **class** `FakeController` — line 71
  - **method** `def __init__(self)` — line 72
  - **method** `def status(self)` — line 82
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 86
  - **method** `def remove_peer(self, public_key)` — line 96
- **function** `def test_status_filters_foreign_peers()` — line 103
- **function** `def test_remove_foreign_peer_is_forbidden()` — line 123
- **function** `def test_add_rolls_back_ownership_when_controller_fails()` — line 137
- **function** `def test_add_updates_session_only_after_controller_success()` — line 164
- **function** `def test_registry_conflict_is_preserved_as_409()` — line 186
- **function** `def test_existing_owned_key_is_rejected_before_reservation()` — line 210
- **function** `def test_admin_status_merges_runtime_and_ownership()` — line 233
- **function** `def test_non_admin_cannot_read_admin_status()` — line 268
- **function** `def test_admin_can_reassign_owner()` — line 282
- **function** `def test_admin_can_create_user()` — line 300
- **function** `def test_admin_cannot_delete_active_account()` — line 317
- **function** `def test_add_reports_consistency_error_when_rollback_fails()` — line 332
- **function** `def test_remove_controller_failure_does_not_touch_ownership()` — line 362
- **function** `def test_remove_persistence_failure_is_partial_success_502()` — line 384

## `tests/client/test_secure_session.py`

- **variable** `K_SESSION` — line 30
- **variable** `SESSION_ID` — line 31
- **variable** `DEFAULT_SECURE_SESSION_CONFIG` — line 36
- **variable** `config` — line 44
- **function** `def new_pair(k_session: bytes = K_SESSION, session_id: bytes = SESSION_ID)` — line 49
- **function** `def test_response_bound_to_its_own_request()` — line 60
- **function** `def test_response_cannot_be_verified_with_different_request()` — line 73
- **function** `def test_response_nonce_is_inherited_from_request_not_from_auth()` — line 97
- **function** `def test_request_counters_strictly_increasing_accepted()` — line 126
- **function** `def test_request_counter_reordering_within_window_is_accepted()` — line 138
- **function** `def test_request_counter_gaps_are_allowed_by_current_protocol()` — line 149
- **function** `def test_response_counter_must_match_request_counter()` — line 172
- **function** `def test_response_replay_detected()` — line 192
- **function** `def test_request_method_tampering()` — line 215
- **function** `def test_request_session_id_tampering()` — line 230
- **function** `def test_response_session_id_tampering()` — line 249
- **function** `def test_same_key_different_session_id_fails()` — line 274
- **function** `def test_different_key_same_session_id_fails()` — line 290
- **function** `def test_different_key_and_session_id_fails()` — line 306
- **function** `def test_request_key_and_response_key_are_independent()` — line 322
- **function** `def test_nonce_has_expected_size()` — line 356
- **function** `def test_request_nonce_tampering_fails()` — line 367
- **function** `def test_verify_request_with_missing_field()` — line 388
- **function** `def test_verify_request_with_non_dict_auth()` — line 406
- **function** `def test_verify_request_with_invalid_base64()` — line 419
- **function** `def test_verify_request_with_non_string_base64_field()` — line 437
- **function** `def test_verify_request_with_wrong_length_nonce()` — line 455
- **function** `def test_verify_request_with_wrong_length_mac()` — line 473
- **function** `def test_verify_request_with_invalid_counter_type()` — line 491
- **function** `def test_verify_request_with_counter_out_of_range()` — line 509
- **function** `def test_invalid_mac_does_not_advance_request_counter()` — line 526
- **function** `def test_invalid_nonce_does_not_advance_request_counter()` — line 548
- **function** `def test_request_path_tampering()` — line 570
- **function** `def test_request_body_tampering()` — line 582
- **function** `def test_response_status_tampering()` — line 594
- **function** `def test_response_body_tampering()` — line 611
- **function** `def test_request_counter_exhaustion()` — line 628
- **function** `def test_non_admin_principal_can_access_only_owned_peers()` — line 721
- **function** `def test_admin_principal_can_access_every_peer()` — line 733
- **function** `def test_session_peer_snapshot_tracks_current_session_changes()` — line 745

## `tests/client/test_secure_session_concurrency.py`

- **variable** `CFG` — line 38
- **variable** `K_SESSION` — line 47
- **variable** `SESSION_ID` — line 48
- **variable** `LISTEN_PATH` — line 49
- **variable** `INTERFACE` — line 50
- **class** `FakePeerService` — line 53
  - **method** `def status(self)` — line 54
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 57
  - **method** `def remove_peer(self, public_key)` — line 60
- **function** `def start_server()` — line 64
- **function** `def stop_server(srv)` — line 82
- **function** `def server()` — line 88
- **function** `def new_sender()` — line 94
- **function** `def sign(sender, method = 'GET', path = '/v1/status', body = b'')` — line 99
- **variable** `SIGN_LOCK` — line 103
- **function** `def sign_serialized(sender, method = 'GET', path = '/v1/status', body = b'')` — line 106
- **function** `def send(srv, auth, method = 'GET', path = '/v1/status', body = b'')` — line 112
- **function** `def test_sequential_requests_all_succeed(server)` — line 137
- **function** `def test_lost_request_does_not_desync(server)` — line 147
- **function** `def test_same_signed_request_sent_concurrently_accepted_once(server, round_)` — line 154
- **function** `def test_retry_with_same_counter_after_lost_response_is_rejected(server)` — line 169
- **function** `def test_python_sender_counters_unique_under_threads()` — line 177
- **function** `def test_reordered_pair_both_accepted_with_window(server)` — line 190
- **function** `def run_parallel(server, signer, n = 64, workers = 16)` — line 199
- **function** `def test_concurrent_requests_report()` — line 205
- **function** `def test_concurrent_requests_all_succeed_serialized_signing(server)` — line 222
- **function** `def test_concurrent_requests_all_succeed_unsynchronized_signing(server)` — line 227

## `tests/client/test_secure_session_policy.py`

- **variable** `K_SESSION` — line 14
- **variable** `SESSION_ID` — line 15
- **class** `FakeClock` — line 18
  - **method** `def __init__(self)` — line 19
  - **method** `def __call__(self)` — line 22
  - **method** `def advance(self, seconds)` — line 25
- **function** `def cfg(**overrides)` — line 29
- **function** `def pair(**overrides)` — line 44
- **function** `def test_reordered_request_within_window_is_accepted()` — line 56
- **function** `def test_request_older_than_window_is_rejected()` — line 69
- **function** `def test_response_can_arrive_out_of_order()` — line 83
- **function** `def test_session_expiry_is_enforced()` — line 103
- **function** `def test_max_request_frequency_is_enforced_without_a_timer_thread()` — line 113
- **function** `def test_frequency_and_timeout_must_fit_counter_capacity()` — line 128

## `tests/client/test_secure_session_threadsefety.py`

- **variable** `CFG` — line 22
- **variable** `K_SESSION` — line 31
- **variable** `SESSION_ID` — line 32
- **function** `def new()` — line 35
- **function** `def run_threads(n, target)` — line 39
- **function** `def test_sender_counters_unique_and_contiguous_under_threads()` — line 55
- **function** `def test_concurrently_created_requests_all_verify_when_delivered_in_order()` — line 65
- **function** `def test_verify_request_same_auth_concurrently_accepted_once(round_)` — line 78
- **function** `def test_verify_response_same_auth_concurrently_accepted_once(round_)` — line 93

## `tests/client/test_wg_client_activator.py`

- **variable** `DEFAULT_SOCKET` — line 10
- **function** `def activation_params()` — line 14
- **function** `def systemd_client_instances()` — line 25
- **function** `def systemd_session_units(session_id)` — line 46
- **function** `def wait_until(predicate, timeout = 5, interval = 0.1)` — line 70
- **function** `def test_activation(activation_params)` — line 80
- **function** `def test_activation_invalid(activation_params)` — line 84
- **function** `def test_activation_timeout(activation_params)` — line 91
- **function** `def test_concurrent_activation(activation_params)` — line 115

## `tests/client/test_wg_client_integration.py`

- **variable** `log` — line 27
- **variable** `ROOT` — line 30
- **variable** `CERT` — line 31
- **variable** `LISTEN_PATH` — line 33
- **variable** `PUBLIC_KEY` — line 36
- **variable** `NOW` — line 38
- **function** `def lifecycle()` — line 41
- **function** `def ipc(lifecycle)` — line 45
- **function** `def make_config(api_port = 0, controller_port = 9)` — line 53
- **function** `def make_packet(**overrides)` — line 84
- **function** `def free_port()` — line 100
- **function** `def test_parse_activation_valid(ipc)` — line 111
- **function** `def test_parse_activation_rejects(overrides, ipc)` — line 150
- **function** `def run_activation(packet, cfg, monkeypatch, lifecycle, *, patch_load_config = True)` — line 155
- **function** `def test_activation_ok_only_after_bind(monkeypatch, caplog, lifecycle, ipc)` — line 193
- **function** `def test_activation_error_when_port_busy(monkeypatch, lifecycle)` — line 222
- **function** `def test_activation_error_on_invalid_packet(monkeypatch, lifecycle)` — line 236
- **function** `def test_activation_reports_unexpected_exception(monkeypatch, lifecycle)` — line 243
- **class** `FakeController` — line 269
  - **method** `def __init__(self)` — line 270
  - **method** `def status(self)` — line 274
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 278
  - **method** `def remove_peer(self, public_key)` — line 282
- **class** `FakeSecureSession` — line 287
  - **method** `def __init__(self)` — line 288
  - **method** `def verify_request(self, auth, method, path, body)` — line 292
  - **method** `def create_response_auth(self, request_auth, status, body)` — line 295
  - **method** `def can_access_peer(self, public_key)` — line 302
  - **method** `def register_peer(self, public_key)` — line 305
  - **method** `def unregister_peer(self, public_key)` — line 308
- **class** `FakeIPC` — line 312
  - **method** `def __init__(self)` — line 313
  - **method** `def register_peer(self, public_key, allowed_ip)` — line 316
  - **method** `def unregister_peer(self, public_key)` — line 320
  - **method** `def ownership_state(self)` — line 324
  - **method** `def reassign_owner(self, public_key, username)` — line 345
  - **method** `def create_user(self, username, password)` — line 352
  - **method** `def delete_user(self, username)` — line 356
- **function** `def api(lifecycle)` — line 362
- **function** `def request(api, method, path, body = None, headers = None)` — line 387
- **function** `def test_status_below_listen_path(api)` — line 408
- **function** `def test_admin_peer_status(api)` — line 415
- **function** `def test_admin_reassign_owner(api)` — line 441
- **function** `def test_admin_create_user(api)` — line 465
- **function** `def test_admin_delete_user(api)` — line 485
- **function** `def test_outside_listen_path_is_404(api)` — line 500
- **function** `def test_interface_mismatch_is_502(api)` — line 507
- **function** `def test_put_decodes_public_key(api)` — line 515
- **function** `def test_delete_decodes_public_key(api)` — line 527
- **function** `def test_put_negative_content_length_is_400(api)` — line 536
- **function** `def test_trace_not_supported(api)` — line 544
- **function** `def test_stop_before_serve_loop_does_not_hang()` — line 550
- **function** `def test_controller_unreachable_is_502()` — line 570
- **function** `def test_controller_timeout_from_config()` — line 588
- **function** `def test_api_rejects_missing_secure_session()` — line 594
- **function** `def run_mock(tmp_path, *args)` — line 604
- **function** `def test_mock_handshake(tmp_path)` — line 619
- **function** `def test_mock_handshake_unknown_peer(tmp_path)` — line 632
- **function** `def test_peer_register_rpc_is_completed_by_control_loop(lifecycle)` — line 640
- **function** `def test_peer_register_on_closed_ipc_is_protocol_error(lifecycle)` — line 700
- **function** `def test_manager_peer_snapshot_normalizes_controller_status()` — line 718
- **function** `def test_manager_peer_snapshot_rejects_ambiguous_allowed_ips()` — line 742

## `tests/e2e/test_js_full_flow.mjs`

- **function** `parseIni` — line 47
- **function** `secureSessionConfig` — line 72
- **function** `requestHttps` — line 89
- **function** `secureRequest` — line 122
- **function** `userPeers` — line 180
- **function** `registryEntry` — line 187
- **function** `findFreeIp` — line 193
- **function** `waitForLoggedOut` — line 210
- **function** `main` — line 226

## `tests/e2e/test_js_user_lifecycle.mjs`

- **function** `parseIni` — line 45
- **function** `secureSessionConfig` — line 69
- **function** `requestHttps` — line 86
- **function** `secureRequest` — line 117
- **function** `waitForLoggedOut` — line 160
- **function** `manageUser` — line 177
- **function** `main` — line 200

## `tests/frontend/test_cross_language_vector.py`

- **variable** `PROJECT_ROOT` — line 12
- **variable** `FRONTEND_DIR` — line 14
- **variable** `INPUT_VECTOR` — line 16
- **variable** `CANONICAL_VECTOR` — line 17
- **variable** `JS_VECTOR_CHECKER` — line 18
- **variable** `PYTHON_VECTOR_GENERATOR` — line 20
- **function** `def load_json(path: Path) -> dict` — line 25
- **function** `def run_python_generator(input_path: Path, output_path: Path) -> None` — line 30
- **function** `def run_js_checker() -> None` — line 51
- **function** `def test_python_vector_matches_canonical_vector()` — line 75
- **function** `def test_javascript_implementation_matches_canonical_vector()` — line 90

## `tests/frontend/test_secure_session_concurrency.test.mjs`

- **function** `newSession` — line 25

## `tests/frontend/wg_secure_session_gen_vectors.py`

- **function** `def hex_to_bytes(value: str) -> bytes` — line 29
- **function** `def bytes_to_hex(value: bytes) -> str` — line 33
- **function** `def body_bytes(section: dict) -> bytes` — line 37
- **function** `def load_json(path: str) -> dict` — line 44
- **function** `def save_json(path: str, value: dict) -> None` — line 49
- **function** `def fixed_nonce_rng(nonce: bytes)` — line 55
- **function** `def generate_vector(input_data: dict) -> dict` — line 68
- **function** `def main() -> None` — line 142

## `tests/test_mock.py`

- **variable** `ROOT` — line 12
- **variable** `MOCK_PROGRAM` — line 13
- **variable** `REAL_WG_PATHS` — line 14
- **variable** `PUBLIC_KEY` — line 19
- **variable** `SECOND_PUBLIC_KEY` — line 20
- **function** `def verify_mock_executable()` — line 24
- **function** `def mock_env(tmp_path)` — line 50
- **function** `def run_mock(mock_env, *args)` — line 58
- **function** `def dump_peers(mock_env)` — line 70
- **function** `def test_initial_state_is_empty(mock_env)` — line 77
- **function** `def test_add_peer(mock_env)` — line 92
- **function** `def test_update_peer(mock_env)` — line 113
- **function** `def test_remove_peer(mock_env)` — line 142
- **function** `def test_remove_unknown_peer_fails(mock_env)` — line 166
- **function** `def test_invalid_commands_are_rejected(mock_env, args)` — line 190
- **function** `def test_handshake_updates_peer_statistics(mock_env)` — line 197
- **function** `def test_state_persists_between_invocations(mock_env)` — line 230
