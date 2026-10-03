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

- `{**: ‹wg_auth_API_handler.py:WGAuthAPIHandler.do_GET.status›, ok: True}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:253
- `{activation: ‹in http.server.rfile.read›('auth'), authenticated: True, k_session: ‹wg_auth_API_handler.py:WGAuthAPIHandler.api›, ok: True, session_id: ‹wg_auth_API_handler.py:WGAuthAPIHandler.api›}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:141
- `{client_id: ‹wg_auth_IPC.py:WGAuthIPC.client_id›∈{'client'|'client_id'}, created_at: ?, k_session: ‹in http.server.rfile.read›('auth'|'login_dir'|'username'), listen_path: ‹wg_auth_IPC.py:WGAuthIPC.l…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:531
- `{error: 'admin principal required', protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, st…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:363
- `{error: 'admin principal required', protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:276
- `{error: 'authentication failed', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:153, wg_auth_API_handler.py:83
- `{error: 'internal server error', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:124, wg_auth_API_handler.py:193
- `{error: 'invalid authentication request', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:102, wg_auth_API_handler.py:171
- `{error: 'logout requires authenticated wg-client sessio…, ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:232
- `{error: 'not found', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:213, wg_auth_API_handler.py:223, wg_auth_API_handler.py:245
- `{error: ?, ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:113, wg_auth_API_handler.py:162, wg_auth_API_handler.py:182
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_cod…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:405
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_cod…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:394, wg_auth_IPC.py:416
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_cod…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:428
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_c…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:311
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_c…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:322
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_c…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:334
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_code: …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:194
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_code: …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:206
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', status_code: …` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:218
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_provisioning_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'ERROR', statu…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:247
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, status: 'ERROR', type: 'STATE_RESULT'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:561
- `{ok: True, response: ‹in http.server.rfile.read›('pub'|'username')}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:73
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_account_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, result: ‹wg_auth_IPC.py:WGAuthIPC._ha…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:438
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, result: ‹wg_auth_IPC.py:WGAuthIPC._…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:344
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, status: 'OK', type: 'PEER_RESULT'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:228
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_provisioning_request.request_id›∈{'request_id'|'utf-8'|b'\n'}, result: ‹wg_auth_IPC.py:WGAuthIP…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:257
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, status: 'OK', type: 'STATE_RESULT'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:569
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STOP'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:592

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

### `wg_auth_API.py:WGAuthAPI._create_server` — http.server.<create http.server.ThreadingHTTPServer>@L440, socket.wrap_socket@L466
- via: .wrap_socket, configparser.ConfigParser, http.server.ThreadingHTTPServer, ssl.SSLContext
- costanti dirette: 'host', 'http', 'port'
- esterni: ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER

### `wg_auth_API_handler.py:WGAuthAPIHandler._read_json` — http.server.headers@L39, http.server.rfile.read@L42
- costanti dirette: '0', 'Content-Length'
- dalla rete: http.server.headers

### `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — http.server.end_headers@L34, http.server.send_header@L32, http.server.send_header@L33, http.server.send_response@L31, http.server.wfile.write@L36
- via: json.dumps
- costanti dirette: ',', ':', 'Content-Length', 'Content-Type', 'application/json', 'utf-8', 200, 400, 401, 404, 405, 409 (+1)
- forme: 17 (vedi sopra)

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_DELETE` — http.server.path@L220

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_GET` — http.server.path@L242

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_POST` — http.server.path@L203, http.server.path@L207

### `wg_auth_IPC.py:WGAuthIPC.activate` — socket.<create socket.socket>@L524, socket.connect@L529
- via: configparser.ConfigParser
- costanti dirette: 'client', 'socket_path'
- esterni: socket.AF_UNIX, socket.SOCK_STREAM

### `wg_auth_IPC.py:WGAuthIPC.close` — socket.close@L631, socket.shutdown@L626
- esterni: socket.SHUT_RDWR

### `wg_auth_IPC.py:WGAuthIPC.receive_packet` — socket.recv@L470
- costanti dirette: 4096

### `wg_auth_IPC.py:WGAuthIPC.send_packet` — socket.sendall@L616
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

