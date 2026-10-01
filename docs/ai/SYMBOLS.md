# Symbols

Structural symbol index extracted mechanically from source files.

## `src/wg_auth/wg_auth.py`

- **variable** `log` — line 11
- **variable** `config_path` — line 12
- **function** `def load_config(path)` — line 13
- **function** `def main()` — line 19

## `src/wg_auth/wg_auth_API.py`

- **variable** `log` — line 9
- **class** `WGAuthAPI` — line 12
  - **method** `def __init__(self, config, lifecycle)` — line 18
  - **method** `def __enter__(self)` — line 34
  - **method** `def __exit__(self, exc_type, exc_value, traceback)` — line 38
  - **method** `def run(self)` — line 41
  - **method** `def stop(self)` — line 47
  - **method** `def get_session_status(self)` — line 57
  - **method** `def start_authentication(self, username, pubU)` — line 74
  - **method** `def finish_authentication(self, authU)` — line 123
  - **method** `def _activation_failed(self, session, ipc)` — line 215
  - **method** `def logout(self, notify_client = True)` — line 238
  - **method** `def _finish_shutdown(self, session, ipc, notify_client = True)` — line 283
  - **method** `def _create_server(self)` — line 314

## `src/wg_auth/wg_auth_API_handler.py`

- **variable** `log` — line 9
- **class** `WGAuthAPIHandler` (BaseHTTPRequestHandler) — line 11
  - **method** `def _send_json(self, status, payload)` — line 14
  - **method** `def _read_json(self)` — line 26
  - **method** `def _handle_auth_start(self)` — line 46
  - **method** `def _handle_auth_verify(self)` — line 118
  - **method** `def do_POST(self)` — line 188
  - **method** `def do_DELETE(self)` — line 202
  - **method** `def do_GET(self)` — line 220

## `src/wg_auth/wg_auth_IPC.py`

- **variable** `log` — line 8
- **variable** `MAX_PACKET_SIZE` — line 11
- **variable** `PROTOCOL_VERSION` — line 12
- **class** `WGAuthIPC` — line 15
  - **method** `def __init__(self, socket_path, client_id, timeout, listen_path, lifecycle)` — line 17
  - **method** `def active(self)` — line 33
  - **method** `def control_loop(self)` — line 36
  - **method** `def receive_packet(self)` — line 101
  - **method** `def parse_packet(self, packet)` — line 130
  - **method** `def activate(self, session_id, k_session)` — line 157
  - **method** `def deactivate(self)` — line 193
  - **method** `def send_packet(self, packet)` — line 204
  - **method** `def close(self)` — line 213

## `src/wg_auth/wg_auth_errors.py`

- **class** `WGAuthError` (Exception) — line 1
  - **method** `def __init__(self, message)` — line 3
- **class** `WGAuthSessionError` (WGAuthError) — line 8
- **class** `WGAuthAuthenticationError` (WGAuthError) — line 12
- **class** `WGAuthProtocolError` (WGAuthError) — line 16

## `src/wg_auth/wg_auth_lifecycle.py`

- **variable** `log` — line 4
- **class** `WGAuthLifecycle` — line 5
  - **method** `def __init__(self, api = None, ipc = None)` — line 7
  - **method** `def request_shutdown(self)` — line 15
  - **method** `def request_session_shutdown(self, notify_client = True)` — line 30
  - **method** `def request_session_start(self)` — line 42

## `src/wg_auth/wg_auth_session.py`

- **variable** `log` — line 13
- **class** `WGAuthSession` — line 16
  - **method** `def __init__(self, username, credential_record, context)` — line 22
  - **method** `def authenticated(self)` — line 36
  - **method** `def session_id(self)` — line 40
  - **method** `def k_session(self)` — line 49
  - **method** `def create_credential_response(self, pubU)` — line 61
  - **method** `def authenticate(self, authU)` — line 112
  - **method** `def logout(self)` — line 152

## `src/wg_client/wg_client.py`

- **variable** `log` — line 24
- **function** `def setup_logging()` — line 27
- **function** `def systemd_notify(message)` — line 36
- **function** `def activate(ipc, lifecycle)` — line 55
- **function** `def main()` — line 126

## `src/wg_client/wg_client_API.py`

- **variable** `log` — line 12
- **class** `WGClientAPI` — line 16
  - **method** `def __init__(self, config, listen_path, session = None, lifecycle = None)` — line 17
  - **method** `def start(self)` — line 63
  - **method** `def bind(self)` — line 68
  - **method** `def serve(self)` — line 109
  - **method** `def stop(self)` — line 122
  - **method** `def close(self)` — line 136

## `src/wg_client/wg_client_API_handler.py`

- **variable** `log` — line 21
- **variable** `MAX_BODY_SIZE` — line 24
- **variable** `PEERS_PREFIX` — line 26
- **variable** `AUTH_SESSION_ID_HEADER` — line 31
- **variable** `AUTH_COUNTER_HEADER` — line 32
- **variable** `AUTH_NONCE_HEADER` — line 33
- **variable** `AUTH_MAC_HEADER` — line 34
- **variable** `_AUTH_MALFORMED_ERRORS` — line 39
- **variable** `_AUTH_REJECTED_ERRORS` — line 47
- **class** `WGClientHTTPServer` (http.server.ThreadingHTTPServer) — line 55
  - **method** `def __init__(self, server_address, handler_class, controller, listen_path, interface, lifecycle, session = None)` — line 56
- **class** `WGClientAPIHandler` (http.server.BaseHTTPRequestHandler) — line 85
  - **method** `def handle_one_request(self)` — line 95
  - **method** `def controller(self)` — line 106
  - **method** `def lifecycle(self)` — line 109
  - **method** `def session(self)` — line 113
  - **method** `def session_lock(self)` — line 117
  - **method** `def api_path(self)` — line 120
  - **method** `def api_target(self)` — line 137
  - **method** `def peer_key(self, path)` — line 162
  - **method** `def log_message(self, format, *args)` — line 171
  - **method** `def request_auth_headers(self)` — line 178
  - **method** `def authenticate_request(self, body)` — line 207
  - **method** `def _authenticated_headers(self, code, body)` — line 253
  - **method** `def send_error(self, code, message = None, explain = None)` — line 281
  - **method** `def send_json(self, code, obj)` — line 341
  - **method** `def do_GET(self)` — line 375
  - **method** `def do_POST(self)` — line 408
  - **method** `def do_DELETE(self)` — line 417
  - **method** `def do_CONNECT(self)` — line 443
  - **method** `def do_PATCH(self)` — line 447
  - **method** `def do_PUT(self)` — line 451

## `src/wg_client/wg_client_IPC.py`

- **variable** `log` — line 8
- **variable** `MAX_PACKET_SIZE` — line 10
- **variable** `PROTOCOL_VERSION` — line 12
- **variable** `MAX_SESSION_TIMEOUT` — line 15
- **variable** `MAX_CLOCK_SKEW` — line 18
- **variable** `LISTEN_PATH_RE` — line 20
- **class** `WGClientIPC` — line 23
  - **method** `def __init__(self, sock, lifecycle)` — line 25
  - **method** `def control_loop(self)` — line 30
  - **method** `def receive_packet(self)` — line 78
  - **method** `def parse_packet(self, packet)` — line 101
  - **method** `def _int_field(self, obj, name)` — line 118
  - **method** `def _hex_field(self, obj, name)` — line 128
  - **method** `def parse_activation(self, obj, now = None)` — line 140
  - **method** `def send_result(self, status, **fields)` — line 191
  - **method** `def _notify_stop(self)` — line 201
  - **method** `def stop(self, notify_shutdown = True)` — line 216

## `src/wg_client/wg_client_activator.py`

- **class** `WGClientActivation` — line 5
  - **method** `def __init__(self, sock, response)` — line 6
  - **method** `def close(self)` — line 10
  - **method** `def __enter__(self)` — line 15
  - **method** `def __exit__(self, exc_type, exc_value, traceback)` — line 18
- **function** `def activate_client(socket_path, k_sess, timeout, client_id, session_id, listen_path)` — line 21

## `src/wg_client/wg_client_config.py`

- **variable** `DEFAULT_CONFIG` — line 7
- **variable** `DEFAULT_SECURE_SESSION_ENABLED` — line 10
- **variable** `DEFAULT_SESSION_ID_SIZE` — line 11
- **variable** `DEFAULT_NONCE_SIZE` — line 12
- **variable** `DEFAULT_SESSION_KEY_SIZE` — line 13
- **variable** `DEFAULT_COUNTER_MIN` — line 14
- **variable** `DEFAULT_COUNTER_MAX` — line 15
- **function** `def load_config()` — line 18

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
- **class** `WGAPIError` (WGClientError) — line 57
- **class** `WGReplayError` (WGProtocolError) — line 63
- **class** `WGMalformedMessageError` (WGProtocolError) — line 67
- **class** `WGInvalidFieldError` (WGProtocolError) — line 72
- **class** `WGInvalidEncodingError` (WGProtocolError) — line 77
- **class** `WGCounterError` (WGProtocolError) — line 82
- **class** `WGCounterExhaustedError` (WGCounterError) — line 87
- **class** `WGInvalidMACError` (WGAuthenticationError) — line 92
- **class** `WGSessionMismatchError` (WGAuthenticationError) — line 97

## `src/wg_client/wg_client_lifecycle.py`

- **variable** `log` — line 4
- **class** `WGClientLifecycle` — line 5
  - **method** `def __init__(self, api = None, ipc = None)` — line 6
  - **method** `def request_shutdown(self, notify_shutdown = True)` — line 13

## `src/wg_client/wg_controller_client.py`

- **class** `WGControllerClient` — line 13
  - **method** `def __init__(self, host, port, ca, cert, key, timeout = 10)` — line 14
  - **method** `def _request(self, method, path, body = None)` — line 24
  - **method** `def status(self)` — line 76
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 81
  - **method** `def remove_peer(self, public_key)` — line 93
- **class** `WGClientClient` — line 101
  - **method** `def __init__(self, host, port, ca, cert, key, timeout = 10, listen_path = None, secure_session = None)` — line 102
  - **method** `def _request(self, method, path, body = None)` — line 118
  - **method** `def status(self)` — line 193
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 198
  - **method** `def remove_peer(self, public_key)` — line 210

## `src/wg_client/wg_secure_session.py`

- **variable** `log` — line 24
- **class** `WGSecureSession` — line 27
  - **method** `def __init__(self, config, k_session: bytes, session_id: bytes | None = None, rng = None)` — line 47
  - **method** `def session_id(self) -> bytes` — line 112
  - **method** `def session_id_b64(self) -> str` — line 117
  - **method** `def _derive_session_seed(self) -> bytes` — line 125
  - **method** `def _derive_key(self, purpose: bytes) -> bytes` — line 134
  - **method** `def create_request_auth(self, method: str, path: str, body: bytes = b'') -> dict` — line 147
  - **method** `def create_response_auth(self, request_auth: dict, status: int, body: bytes = b'') -> dict` — line 204
  - **method** `def verify_request(self, auth: dict, method: str, path: str, body: bytes = b'') -> bool` — line 262
  - **method** `def verify_response(self, auth: dict, request_auth: dict, status: int, body: bytes = b'') -> bool` — line 329
  - **method** `def _validate_auth_structure(auth: dict, required_fields: tuple) -> None` — line 406
  - **method** `def _validate_session_id(self, value) -> bytes` — line 416
  - **method** `def _validate_counter(self, value) -> int` — line 426
  - **method** `def _validate_nonce(self, value) -> bytes` — line 435
  - **method** `def _validate_mac(self, value) -> bytes` — line 445
  - **method** `def _validate_request_auth(self, auth: dict) -> dict` — line 455
  - **method** `def _validate_response_auth(self, auth: dict) -> dict` — line 469
  - **method** `def _request_message(self, counter: int, nonce: bytes, method: str, path: str, body: bytes) -> bytes` — line 492
  - **method** `def _response_message(self, counter: int, nonce: bytes, status: int, body: bytes) -> bytes` — line 515
  - **method** `def _b64(value: bytes) -> str` — line 541
  - **method** `def _unb64(value: str) -> bytes` — line 546

## `src/wg_frontend/check_vectors.mjs`

- **function** `assertEqual` — line 30
- **function** `main` — line 42

## `src/wg_frontend/wg_auth_session.js`

- **class** `WGAuthSession` — line 1

## `src/wg_frontend/wg_client_errors.js`

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

## `src/wg_frontend/wg_secure_session.js`

- **function** `getSubtle` — line 55
- **function** `getRandomBytes` — line 62
- **function** `concatBytes` — line 75
- **function** `bytesToHex` — line 86
- **function** `hexToBytes` — line 92
- **function** `b64encode` — line 105
- **function** `b64decode` — line 113
- **function** `sha256` — line 134
- **class** `WGSecureSession` — line 150
- **function** `bytesEqual` — line 545

## `src/wg_manager/wg_manager.py`

- **variable** `CONFIG` — line 6
- **variable** `WG_PROGRAM` — line 7
- **function** `def log(msg)` — line 13
- **class** `E` (Exception) — line 17
  - **method** `def __init__(self, code, msg)` — line 18
- **function** `def cfg()` — line 22
- **function** `def reply(s, code, obj)` — line 35
- **function** `def request(s)` — line 43
- **function** `def wg(args)` — line 78
- **function** `def key(k)` — line 93
- **function** `def peers(interface)` — line 103
- **function** `def add(c, o)` — line 122
- **function** `def remove(c, pk)` — line 142
- **function** `def dispatch(c, m, t, b)` — line 150
- **function** `def systemd_socket()` — line 165
- **function** `def tls(c)` — line 178
- **function** `def main()` — line 191

## `tests/auth/js/client_cli.js`

- **function** `loadConfig` — line 7
- **function** `main` — line 46

## `tests/auth/js/opaque_client.js`

- **class** `OpaqueClient` — line 4

## `tests/auth/js/wg_auth_client.js`

- **class** `WGAuthHTTPClient` — line 7

## `tests/auth/test_wg_auth.py`

- **variable** `AUTH_URL` — line 11
- **variable** `VALID_ID` — line 13
- **variable** `INVALID_ID` — line 14
- **variable** `CLIENT_SERVICE_PREFIX` — line 16
- **variable** `REQUEST_TIMEOUT` — line 18
- **variable** `POLL_INTERVAL` — line 19
- **variable** `POLL_TIMEOUT` — line 20
- **class** `TestFailure` (Exception) — line 23
- **function** `def log(message)` — line 27
- **function** `def success(message)` — line 31
- **function** `def fail(message)` — line 35
- **function** `def request(method, path, payload = None)` — line 40
- **function** `def systemctl(*args)` — line 93
- **function** `def client_services()` — line 104
- **function** `def active_client_services()` — line 140
- **function** `def wait_for_client_service(expected, description)` — line 148
- **function** `def expect_status(expected_http, expected_authenticated)` — line 181
- **function** `def main()` — line 203

## `tests/client/test_auth_client.py`

- **variable** `CLIENT_CONFIG` — line 17
- **function** `def set_secure_session(enabled: bool)` — line 20
- **function** `def secure_session_config()` — line 33
- **function** `def configure_client()` — line 41
- **function** `def make_key(value)` — line 43
- **function** `def expect_error(func, status, message)` — line 51
- **variable** `DEFAULT_SOCKET` — line 62
- **function** `def activation_params()` — line 64
- **function** `def client(activation_params)` — line 79
- **function** `def peer_data()` — line 99
- **function** `def test_params(client, peer_data, activation_params)` — line 112
- **function** `def test_remove_peer(client: WGClientClient, peer_data, activation_params)` — line 131
- **function** `def test_add_peer_errors(client: WGClientClient, peer_data, activation_params)` — line 158
- **function** `def test_add_peer_and_verify(client: WGClientClient, peer_data, activation_params)` — line 219
- **function** `def test_authenticated_status(activation_params, client)` — line 244

## `tests/client/test_client.py`

- **variable** `CLIENT_CONFIG` — line 20
- **function** `def set_secure_session(enabled: bool)` — line 23
- **function** `def secure_session_config()` — line 35
- **function** `def configure_client()` — line 43
- **function** `def configure_client()` — line 48
- **function** `def make_key(value)` — line 51
- **function** `def expect_error(func, status, message)` — line 59
- **variable** `DEFAULT_SOCKET` — line 70
- **function** `def activation_params()` — line 72
- **function** `def client()` — line 87
- **function** `def peer_data()` — line 97
- **function** `def test_params(client, peer_data, activation_params)` — line 110
- **function** `def test_remove_peer(client: WGClientClient, peer_data, activation_params)` — line 129
- **function** `def test_add_peer_errors(client: WGClientClient, peer_data, activation_params)` — line 156
- **function** `def test_add_peer_and_verify(client: WGClientClient, peer_data, activation_params)` — line 217
- **function** `def test_status(client: WGClientClient, activation_params) -> Any | None` — line 242

## `tests/client/test_client_API.py`

- **variable** `LISTEN_PATH` — line 12
- **function** `def main()` — line 15

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
- **function** `def test_request_counter_lower_than_last_accepted_fails()` — line 138
- **function** `def test_request_counter_gaps_are_allowed_by_current_protocol()` — line 154
- **function** `def test_response_counter_must_match_request_counter()` — line 179
- **function** `def test_response_replay_detected()` — line 199
- **function** `def test_request_method_tampering()` — line 222
- **function** `def test_request_session_id_tampering()` — line 237
- **function** `def test_response_session_id_tampering()` — line 256
- **function** `def test_same_key_different_session_id_fails()` — line 281
- **function** `def test_different_key_same_session_id_fails()` — line 297
- **function** `def test_different_key_and_session_id_fails()` — line 313
- **function** `def test_request_key_and_response_key_are_independent()` — line 329
- **function** `def test_nonce_has_expected_size()` — line 363
- **function** `def test_request_nonce_tampering_fails()` — line 374
- **function** `def test_verify_request_with_missing_field()` — line 395
- **function** `def test_verify_request_with_non_dict_auth()` — line 413
- **function** `def test_verify_request_with_invalid_base64()` — line 426
- **function** `def test_verify_request_with_non_string_base64_field()` — line 444
- **function** `def test_verify_request_with_wrong_length_nonce()` — line 462
- **function** `def test_verify_request_with_wrong_length_mac()` — line 480
- **function** `def test_verify_request_with_invalid_counter_type()` — line 498
- **function** `def test_verify_request_with_counter_out_of_range()` — line 516
- **function** `def test_invalid_mac_does_not_advance_request_counter()` — line 533
- **function** `def test_invalid_nonce_does_not_advance_request_counter()` — line 555
- **function** `def test_request_path_tampering()` — line 577
- **function** `def test_request_body_tampering()` — line 589
- **function** `def test_response_status_tampering()` — line 601
- **function** `def test_response_body_tampering()` — line 618
- **function** `def test_request_counter_exhaustion()` — line 635

## `tests/client/test_wg_client_activator.py`

- **variable** `DEFAULT_SOCKET` — line 12
- **function** `def activation_params()` — line 16
- **function** `def systemd_client_instances()` — line 30
- **function** `def systemd_session_units(session_id)` — line 51
- **function** `def wait_until(predicate, timeout = 5, interval = 0.1)` — line 75
- **function** `def test_activation(activation_params)` — line 85
- **function** `def test_activation_invalid(activation_params)` — line 89
- **function** `def test_activation_timeout(activation_params)` — line 96
- **function** `def test_concurrent_activation(activation_params)` — line 120

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
- **function** `def free_port()` — line 98
- **function** `def test_parse_activation_valid(ipc)` — line 109
- **function** `def test_parse_activation_rejects(overrides, ipc)` — line 137
- **function** `def run_activation(packet, cfg, monkeypatch, lifecycle)` — line 142
- **function** `def test_activation_ok_only_after_bind(monkeypatch, caplog, lifecycle, ipc)` — line 165
- **function** `def test_activation_error_when_port_busy(monkeypatch, lifecycle)` — line 194
- **function** `def test_activation_error_on_invalid_packet(monkeypatch, lifecycle)` — line 208
- **class** `FakeController` — line 220
  - **method** `def __init__(self)` — line 221
  - **method** `def status(self)` — line 225
  - **method** `def add_peer(self, public_key, allowed_ip)` — line 229
  - **method** `def remove_peer(self, public_key)` — line 233
- **function** `def api(lifecycle)` — line 239
- **function** `def request(api, method, path, body = None, headers = None)` — line 260
- **function** `def test_status_below_listen_path(api)` — line 275
- **function** `def test_outside_listen_path_is_404(api)` — line 282
- **function** `def test_interface_mismatch_is_502(api)` — line 289
- **function** `def test_put_decodes_public_key(api)` — line 297
- **function** `def test_delete_decodes_public_key(api)` — line 306
- **function** `def test_put_negative_content_length_is_400(api)` — line 315
- **function** `def test_trace_not_supported(api)` — line 323
- **function** `def test_stop_before_serve_loop_does_not_hang()` — line 329
- **function** `def test_controller_unreachable_is_502()` — line 349
- **function** `def test_controller_timeout_from_config()` — line 367
- **function** `def run_mock(tmp_path, *args)` — line 378
- **function** `def test_mock_handshake(tmp_path)` — line 393
- **function** `def test_mock_handshake_unknown_peer(tmp_path)` — line 406

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

## `tests/frontend/wg_secure_session_gen_vectors.py`

- **function** `def hex_to_bytes(value: str) -> bytes` — line 29
- **function** `def bytes_to_hex(value: bytes) -> str` — line 33
- **function** `def body_bytes(section: dict) -> bytes` — line 37
- **function** `def load_json(path: str) -> dict` — line 44
- **function** `def save_json(path: str, value: dict) -> None` — line 49
- **function** `def fixed_nonce_rng(nonce: bytes)` — line 55
- **function** `def generate_vector(input_data: dict) -> dict` — line 68
- **function** `def main() -> None` — line 142

## `tests/test_http_handler.py`

- **variable** `HOST` — line 10
- **variable** `PORT` — line 11
- **variable** `CERT_FILE` — line 13
- **variable** `KEY_FILE` — line 14
- **variable** `CA_FILE` — line 15
- **variable** `log` — line 18
- **class** `DummyServer` — line 21
  - **method** `def __init__(self, host, port)` — line 30
- **function** `def create_tls_context()` — line 35
- **function** `def handle_connection(connection, address, context)` — line 62
- **function** `def main()` — line 116
