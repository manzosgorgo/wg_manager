# Connections

Generated mechanically by `tools/project_index.py`.

> **Observational only.**
> This document describes communication resources and their
> detected protocol layers.
> It is not a normative architecture specification.

## Summary

- Production connections: **7**
- Test connections: **4**

## Production connections

### connection-001

- **Kind:** http-server
- **Role:** server
- **Handler:** `WGAuthAPIHandler`

**Layers:**
- TCP
- HTTP

**Variables:**
- `server`

**Files:**
- `/home/main/Desktop/wg_manager/src/wg_auth/wg_auth_API.py`
- `src/wg_auth/wg_auth_API.py`
- `src/wg_auth/wg_auth_API_handler.py`

**Symbols:**
- `WGAuthAPI._create_server`

**Evidence:**
- `src/wg_auth/wg_auth_API.py:312` HTTP_SERVER `ThreadingHTTPServer((self.config['http']['host'], int(self.config['http']['port'])), WGAuthAPIHandler)`

**Message surfaces:**
- **HTTP**
  - `WGAuthAPIHandler._handle_auth_start()`
    - **Inputs:** `request.pub`, `request.username`
    - **Outputs:** `{ok, error}`, `{ok, response}`
  - `WGAuthAPIHandler._handle_auth_verify()`
    - **Inputs:** `request.auth`
    - **Outputs:** `{ok, authenticated, session_id, k_session, activation}`, `{ok, error}`
  - `WGAuthAPIHandler.do_DELETE()`
    - **Outputs:** `{ok}`, `{ok, error}`
  - `WGAuthAPIHandler.do_GET()`
    - **Outputs:** `{ok}`, `{ok, error}`
  - `WGAuthAPIHandler.do_POST()`
    - **Outputs:** `{ok, error}`

### connection-002

- **Kind:** socket
- **Transport:** UNIX

**Layers:**
- socket

**Files:**
- `/home/main/Desktop/wg_manager/src/wg_auth/wg_auth_IPC.py`
- `src/wg_auth/wg_auth_IPC.py`

**Symbols:**
- `WGAuthIPC.activate`

**Evidence:**
- `src/wg_auth/wg_auth_IPC.py:164` SOCKET_CREATE `socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)`

**Message surfaces:**
- **IPC**
  - `WGAuthIPC.activate()`
    - **Outputs:** `{protocol_version, session_id, k_session, client_id, timeout, listen_path, principal, created_at}`

### connection-003

- **Kind:** socket
- **Role:** client
- **Transport:** UNIX-DGRAM

**Layers:**
- socket

**Variables:**
- `sock`

**Files:**
- `/home/main/Desktop/wg_manager/src/wg_client/wg_client.py`
- `src/wg_client/wg_client.py`

**Symbols:**
- `systemd_notify`

**Evidence:**
- `src/wg_client/wg_client.py:45` SOCKET_CREATE `socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)`
- `src/wg_client/wg_client.py:48` CONNECT `sock.connect(notify_socket)`
- `src/wg_client/wg_client.py:49` SENDALL `sock.sendall(message.encode())`
- `src/wg_client/wg_client.py:52` CLOSE `sock.close()`

### connection-004

- **Kind:** socket
- **Transport:** UNIX

**Layers:**
- socket

**Variables:**
- `sock`

**Files:**
- `/home/main/Desktop/wg_manager/src/wg_client/wg_client.py`
- `src/wg_client/wg_client.py`

**Symbols:**
- `main`

**Evidence:**
- `src/wg_client/wg_client.py:150` SOCKET_CREATE `socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, fileno=os.dup(sys.stdin.fileno()))`

### connection-005

- **Kind:** socket
- **Role:** client
- **Transport:** UNIX

**Layers:**
- socket

**Variables:**
- `sock`

**Files:**
- `/home/main/Desktop/wg_manager/src/wg_client/wg_client_activator.py`
- `src/wg_client/wg_client_activator.py`

**Symbols:**
- `activate_client`

**Evidence:**
- `src/wg_client/wg_client_activator.py:48` SOCKET_CREATE `socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)`
- `src/wg_client/wg_client_activator.py:54` CONNECT `sock.connect(socket_path)`
- `src/wg_client/wg_client_activator.py:55` SENDALL `sock.sendall(payload)`
- `src/wg_client/wg_client_activator.py:79` CLOSE `sock.close()`

**Message surfaces:**
- **INTERNAL**
  - `activate_client()`
    - **Outputs:** `{protocol_version, session_id, k_session, client_id, timeout, created_at, listen_path, principal}`

### connection-006

- **Kind:** http-client
- **Role:** client

**Layers:**
- TCP
- TLS
- HTTP

**Variables:**
- `conn`

**Files:**
- `/home/main/Desktop/wg_manager/src/wg_client/wg_controller_client.py`
- `src/wg_client/wg_controller_client.py`

**Symbols:**
- `WGControllerClient._request`

**Evidence:**
- `src/wg_client/wg_controller_client.py:32` HTTP_CLIENT `http.client.HTTPSConnection(self.host, self.port, context=self.tls, timeout=self.timeout)`
- `src/wg_client/wg_controller_client.py:74` CLOSE `conn.close()`

### connection-007

- **Kind:** http-client
- **Role:** client

**Layers:**
- TCP
- TLS
- HTTP

**Variables:**
- `conn`

**Files:**
- `/home/main/Desktop/wg_manager/src/wg_client/wg_controller_client.py`
- `src/wg_client/wg_controller_client.py`

**Symbols:**
- `WGClientClient._request`

**Evidence:**
- `src/wg_client/wg_controller_client.py:126` HTTP_CLIENT `http.client.HTTPSConnection(self.host, self.port, context=self.tls, timeout=self.timeout)`
- `src/wg_client/wg_controller_client.py:191` CLOSE `conn.close()`

## Test connections

### connection-008

- **Kind:** http-client
- **Role:** client
- **Transport:** TCP

**Layers:**
- TCP
- HTTP

**Variables:**
- `conn`

**Files:**
- `/home/main/Desktop/wg_manager/tests/client/test_secure_session_concurrency.py`
- `tests/client/test_secure_session_concurrency.py`

**Symbols:**
- `send`

**Evidence:**
- `tests/client/test_secure_session_concurrency.py:120` HTTP_CLIENT `http.client.HTTPConnection('127.0.0.1', port, timeout=5)`
- `tests/client/test_secure_session_concurrency.py:127` CLOSE `conn.close()`

### connection-009

- **Kind:** socket
- **Transport:** UNIX

**Layers:**
- socket

**Variables:**
- `sock`

**Files:**
- `/home/main/Desktop/wg_manager/tests/client/test_wg_client_integration.py`
- `tests/client/test_wg_client_integration.py`

**Symbols:**
- `ipc`

**Evidence:**
- `tests/client/test_wg_client_integration.py:46` SOCKET_CREATE `socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)`
- `tests/client/test_wg_client_integration.py:50` CLOSE `sock.close()`

### connection-010

- **Kind:** http-client
- **Role:** client

**Layers:**
- TCP
- TLS
- HTTP

**Variables:**
- `conn`

**Files:**
- `/home/main/Desktop/wg_manager/tests/client/test_wg_client_integration.py`
- `tests/client/test_wg_client_integration.py`

**Symbols:**
- `request`

**Evidence:**
- `tests/client/test_wg_client_integration.py:298` HTTP_CLIENT `http.client.HTTPSConnection('127.0.0.1', port, context=ctx, timeout=5)`
- `tests/client/test_wg_client_integration.py:305` CLOSE `conn.close()`

### connection-011

- **Kind:** socket
- **Transport:** TCP

**Layers:**
- socket

**Variables:**
- `server_socket`

**Files:**
- `/home/main/Desktop/wg_manager/tests/test_http_handler.py`
- `tests/test_http_handler.py`

**Symbols:**
- `main`

**Evidence:**
- `tests/test_http_handler.py:127` SOCKET_CREATE `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`
- `tests/test_http_handler.py:138` BIND `server_socket.bind((HOST, PORT))`
- `tests/test_http_handler.py:142` LISTEN `server_socket.listen(1)`
- `tests/test_http_handler.py:153` ACCEPT `server_socket.accept()`
- `tests/test_http_handler.py:165` CLOSE `server_socket.close()`
