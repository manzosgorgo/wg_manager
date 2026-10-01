# Dependencies

This file is generated automatically.

## `src/wg_auth/wg_auth.py`

- `configparser`
- `logging`
- `src.wg_auth.wg_auth_IPC`
- `src.wg_auth.wg_auth_lifecycle`
- `sys`
- `threading`
- `wg_auth_API`
- `wg_auth_session`

## `src/wg_auth/wg_auth_API.py`

- `http.server`
- `logging`
- `src.wg_auth.wg_auth_API_handler`
- `src.wg_auth.wg_auth_IPC`
- `src.wg_auth.wg_auth_errors`
- `src.wg_auth.wg_auth_session`
- `ssl`
- `threading`

## `src/wg_auth/wg_auth_API_handler.py`

- `http.server`
- `json`
- `logging`
- `src.wg_auth.wg_auth_errors`

## `src/wg_auth/wg_auth_IPC.py`

- `json`
- `logging`
- `socket`
- `src.wg_auth.wg_auth_errors`
- `time`

## `src/wg_auth/wg_auth_lifecycle.py`

- `logging`
- `threading`

## `src/wg_auth/wg_auth_session.py`

- `logging`
- `opaque`
- `secrets`
- `src.wg_auth.wg_auth_errors`

## `src/wg_client/wg_client.py`

- `logging`
- `os`
- `re`
- `socket`
- `src.wg_client.wg_client_API`
- `src.wg_client.wg_client_IPC`
- `src.wg_client.wg_client_config`
- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_client_lifecycle`
- `src.wg_client.wg_secure_session`
- `sys`
- `systemd`
- `threading`
- `time`

## `src/wg_client/wg_client_API.py`

- `logging`
- `src.wg_client.wg_client_API_handler`
- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_client_lifecycle`
- `src.wg_client.wg_controller_client`
- `ssl`

## `src/wg_client/wg_client_API_handler.py`

- `datetime`
- `http`
- `http.server`
- `json`
- `logging`
- `src.wg_client.wg_client_errors`
- `threading`
- `urllib.parse`

## `src/wg_client/wg_client_IPC.py`

- `json`
- `logging`
- `re`
- `socket`
- `src.wg_client.wg_client_errors`
- `time`

## `src/wg_client/wg_client_activator.py`

- `json`
- `socket`
- `time`

## `src/wg_client/wg_client_config.py`

- `configparser`
- `math`
- `os`

## `src/wg_client/wg_client_lifecycle.py`

- `logging`
- `threading`

## `src/wg_client/wg_controller_client.py`

- `http.client`
- `json`
- `logging`
- `src.wg_client.wg_client_API_handler`
- `src.wg_client.wg_client_errors`
- `ssl`
- `urllib.parse`

## `src/wg_client/wg_secure_session.py`

- `base64`
- `binascii`
- `cryptography.hazmat.primitives`
- `cryptography.hazmat.primitives.kdf.hkdf`
- `hashlib`
- `hmac`
- `logging`
- `math`
- `secrets`
- `src.wg_client.wg_client_errors`
- `threading`
- `time`

## `src/wg_frontend/check_vectors.mjs`

- `./wg_client_errors.js`
- `./wg_secure_session.js`
- `node:crypto`
- `node:fs`

## `src/wg_manager/wg_manager.py`

- `base64`
- `configparser`
- `http`
- `ipaddress`
- `json`
- `os`
- `socket`
- `ssl`
- `subprocess`
- `sys`
- `urllib.parse`

## `tests/auth/js/client_cli.js`

- `./wg_auth_client`
- `fs`
- `path`

## `tests/auth/js/opaque_client.js`

- `../../../vendor/libopaque/libopaque.js`

## `tests/auth/js/wg_auth_client.js`

- `./opaque_client`
- `fs`
- `https`

## `tests/auth/test_wg_auth.py`

- `json`
- `ssl`
- `subprocess`
- `sys`
- `time`
- `urllib.error`
- `urllib.request`

## `tests/client/test_auth_client.py`

- `base64`
- `ipaddress`
- `pathlib`
- `pytest`
- `src.wg_client`
- `src.wg_client.wg_client_activator`
- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_controller_client`
- `src.wg_client.wg_secure_session`
- `typing`
- `unittest`

## `tests/client/test_client.py`

- `base64`
- `ipaddress`
- `pathlib`
- `pytest`
- `src.wg_client`
- `src.wg_client.wg_client_activator`
- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_controller_client`
- `src.wg_client.wg_secure_session`
- `typing`
- `unittest`

## `tests/client/test_client_API.py`

- `logging`
- `os`
- `src.wg_client.wg_client_API`
- `src.wg_client.wg_client_config`
- `threading`
- `time`

## `tests/client/test_secure_session.py`

- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_secure_session`

## `tests/client/test_secure_session_concurrency.py`

- `collections`
- `concurrent.futures`
- `http.client`
- `pytest`
- `src.wg_client.wg_client_API_handler`
- `src.wg_client.wg_secure_session`
- `threading`

## `tests/client/test_secure_session_policy.py`

- `pytest`
- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_secure_session`

## `tests/client/test_secure_session_threadsefety.py`

- `concurrent.futures`
- `pytest`
- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_secure_session`
- `threading`

## `tests/client/test_wg_client_activator.py`

- `asyncio`
- `concurrent.futures`
- `pytest`
- `src.wg_client.wg_client_activator`
- `subprocess`
- `threading`
- `time`

## `tests/client/test_wg_client_integration.py`

- `base64`
- `http.client`
- `json`
- `logging`
- `os`
- `pathlib`
- `pytest`
- `socket`
- `src.wg_client`
- `src.wg_client.wg_client_API`
- `src.wg_client.wg_client_IPC`
- `src.wg_client.wg_client_errors`
- `src.wg_client.wg_client_lifecycle`
- `src.wg_client.wg_controller_client`
- `ssl`
- `subprocess`
- `sys`
- `threading`
- `time`
- `urllib.parse`

## `tests/frontend/test_cross_language_vector.py`

- `json`
- `pathlib`
- `pytest`
- `shutil`
- `subprocess`
- `tempfile`

## `tests/frontend/test_secure_session_concurrency.test.mjs`

- `../../src/wg_frontend/wg_secure_session.js`
- `node:assert`
- `node:crypto`
- `node:test`

## `tests/frontend/wg_secure_session_gen_vectors.py`

- `hashlib`
- `hmac`
- `json`
- `src.wg_client.wg_secure_session`
- `sys`

## `tests/test_http_handler.py`

- `logging`
- `socket`
- `ssl`
- `tests.client.test_wg_handler`

## `tests/test_mock.py`

- `base64`
- `os`
- `pathlib`
- `pytest`
- `subprocess`
- `sys`
