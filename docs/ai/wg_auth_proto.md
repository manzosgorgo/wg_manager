# Snapshot del protocollo (passo 2)

- Sink analizzati: 10
- Nodi: attr=11, const=52, ext=6, in=2, param=16, shape=38, sink=10, var=33, xf=24 · archi: 326

## Canali (sink con lo stesso ricevente)

- **C1** `wg_auth_IPC.py:WGAuthIPC.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_auth_IPC.py:WGAuthIPC.activate` (socket.<create socket.socket>, socket.connect)
  - `wg_auth_IPC.py:WGAuthIPC.close` (socket.close, socket.shutdown)
  - `wg_auth_IPC.py:WGAuthIPC.receive_packet` (socket.recv)
  - `wg_auth_IPC.py:WGAuthIPC.send_packet` (socket.sendall)
- **C2** `handler:wg_auth_API_handler.py:WGAuthAPIHandler`
  - `wg_auth_API_handler.py:WGAuthAPIHandler._read_json` (http.server.headers, http.server.rfile.read)
  - `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` (http.server.end_headers, http.server.send_header, http.server.send_response, http.server.wfile.write)
  - `wg_auth_API_handler.py:WGAuthAPIHandler.do_DELETE` (http.server.path)
  - `wg_auth_API_handler.py:WGAuthAPIHandler.do_GET` (http.server.path)
  - `wg_auth_API_handler.py:WGAuthAPIHandler.do_POST` (http.server.path)
- **C3** `wg_auth_API.py:WGAuthAPI._create_server.context` — ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext()
  - `wg_auth_API.py:WGAuthAPI._create_server` (http.server.<create http.server.ThreadingHTTPServer>, socket.wrap_socket)

## Forme dei messaggi (dict che arrivano ai sink)

- `{**: ‹wg_auth_API_handler.py:WGAuthAPIHandler.do_GET.status›, ok: True}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:233
- `{activation: ‹in http.server.rfile.read›('auth'), authenticated: True, k_session: ‹wg_auth_API_handler.py:WGAuthAPIHandler.api›, ok: True, session_id: ‹wg_auth_API_handler.py:WGAuthAPIHandler.api›}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:130
- `{client_id: ‹wg_auth_IPC.py:WGAuthIPC.client_id›∈{'client'|'client_id'}, created_at: ?, k_session: ‹in http.server.rfile.read›('auth'|'login_dir'|'username'), listen_path: ‹wg_auth_IPC.py:WGAuthIPC.l…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:502
- `{error: 'admin principal required', protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, st…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:343
- `{error: 'admin principal required', protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:256
- `{error: 'authentication failed', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:142, wg_auth_API_handler.py:72
- `{error: 'internal server error', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:113, wg_auth_API_handler.py:182
- `{error: 'invalid authentication request', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:160, wg_auth_API_handler.py:91
- `{error: 'logout requires authenticated wg-client sessio…, ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:215
- `{error: 'not found', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:199, wg_auth_API_handler.py:206, wg_auth_API_handler.py:225
- `{error: ?, ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:102, wg_auth_API_handler.py:151, wg_auth_API_handler.py:171
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_cod…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:385
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_cod…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:374, wg_auth_IPC.py:396
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_cod…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:408
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_c…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:291
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_c…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:302
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_c…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:314
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_code: …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:174
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_code: …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:186
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_code: …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:198
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_provisioning_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', statu…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:227
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, status: 'ERROR', type: 'STATE_RESULT'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:532
- `{ok: True, response: ‹in http.server.rfile.read›('pub'|'username')}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:62
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, result: ‹wg_auth_IPC.py:WGAuthIPC._ha…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:418
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, result: ‹wg_auth_IPC.py:WGAuthIPC._…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:324
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'OK', type: 'PEER_RESULT'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:208
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_provisioning_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, result: ‹wg_auth_IPC.py:WGAuthIP…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:237
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, status: 'OK', type: 'STATE_RESULT'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:540
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STOP'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:560

## Cosa accettano i parametri (valori costanti che possono assumere)

- `wg_auth_API_handler.py:WGAuthAPIHandler._send_json(status)` ∈ {200 | 400 | 401 | 404 | 405 | 409 | 500}
- `wg_auth_IPC.py:WGAuthIPC.__init__(principal)` ∈ {'auth' | 'login_dir' | 'username' | b'wg-manager'}
- `wg_auth_IPC.py:WGAuthIPC.activate(k_session)` ∈ {'auth' | 'login_dir' | 'username' | b'wg-manager'}
- `wg_auth_IPC.py:WGAuthIPC.activate(session_id)` ∈ {'auth' | 'login_dir' | 'username' | b'wg-manager'}
- `wg_auth_IPC.py:WGAuthIPC.__init__(client_id)` ∈ {'client' | 'client_id'}
- `wg_auth_IPC.py:WGAuthIPC.__init__(listen_path)` ∈ {'client' | 'listen_path'}
- `wg_auth_IPC.py:WGAuthIPC.__init__(socket_path)` ∈ {'client' | 'socket_path'}
- `wg_auth_IPC.py:WGAuthIPC.__init__(timeout)` ∈ {'client' | 'timeout'}
- `wg_auth_IPC.py:WGAuthIPC._handle_account_request(request)` ∈ {'utf-8' | b'\n'}
- `wg_auth_IPC.py:WGAuthIPC._handle_ownership_request(request)` ∈ {'utf-8' | b'\n'}
- `wg_auth_IPC.py:WGAuthIPC._handle_peer_request(request)` ∈ {'utf-8' | b'\n'}
- `wg_auth_IPC.py:WGAuthIPC._handle_provisioning_request(request)` ∈ {'utf-8' | b'\n'}

## Sink

### `wg_auth_API.py:WGAuthAPI._create_server` — http.server.<create http.server.ThreadingHTTPServer>@L402, socket.wrap_socket@L428
- via: .wrap_socket, configparser.ConfigParser, http.server.ThreadingHTTPServer, ssl.SSLContext
- costanti dirette: 'host', 'http', 'port'
- esterni: ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER

### `wg_auth_API_handler.py:WGAuthAPIHandler._read_json` — http.server.headers@L28, http.server.rfile.read@L31
- costanti dirette: '0', 'Content-Length'
- dalla rete: http.server.headers

### `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — http.server.end_headers@L23, http.server.send_header@L21, http.server.send_header@L22, http.server.send_response@L20, http.server.wfile.write@L25
- via: json.dumps
- costanti dirette: ',', ':', 'Content-Length', 'Content-Type', 'application/json', 'utf-8', 200, 400, 401, 404, 405, 409 (+1)
- forme: 17 (vedi sopra)

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_DELETE` — http.server.path@L203

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_GET` — http.server.path@L222

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_POST` — http.server.path@L189, http.server.path@L193

### `wg_auth_IPC.py:WGAuthIPC.activate` — socket.<create socket.socket>@L495, socket.connect@L500
- via: configparser.ConfigParser
- costanti dirette: 'client', 'socket_path'
- esterni: socket.AF_UNIX, socket.SOCK_STREAM

### `wg_auth_IPC.py:WGAuthIPC.close` — socket.close@L593, socket.shutdown@L588
- esterni: socket.SHUT_RDWR

### `wg_auth_IPC.py:WGAuthIPC.receive_packet` — socket.recv@L447
- costanti dirette: 4096

### `wg_auth_IPC.py:WGAuthIPC.send_packet` — socket.sendall@L581
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 21 (vedi sopra)

## Intersezioni (nodi condivisi da piu' sink)

- attr `wg_auth_API.py:WGAuthAPI.config` → 3 sink: `wg_auth_API.py:WGAuthAPI._create_server`, `wg_auth_IPC.py:WGAuthIPC.activate`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- var `wg_auth_API_handler.py:WGAuthAPIHandler._handle_auth_start.username` → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`

### Valori condivisi

- const ',' → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- const ':' → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- const 'Content-Length' → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._read_json`, `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`
- const 'auth' → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- const 'client' → 2 sink: `wg_auth_IPC.py:WGAuthIPC.activate`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- const 'utf-8' → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- const 404 → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- const 409 → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- const 500 → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`

