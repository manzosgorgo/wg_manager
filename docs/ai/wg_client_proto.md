# Snapshot del protocollo (passo 2)

- Sink analizzati: 22
- Nodi: attr=13, const=69, ext=12, in=4, open=13, param=41, shape=18, sink=22, var=54, xf=27 · archi: 400

## Canali (sink con lo stesso ricevente)

- **C1** `<senza ricevente>`
  - `wg_client.py:main` (socket.<create socket.socket>)
- **C2** `wg_client_IPC.py:WGClientIPC.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._notify_stop` (socket.sendall)
  - `wg_client_IPC.py:WGClientIPC.receive_packet` (socket.recv)
  - `wg_client_IPC.py:WGClientIPC.send_result` (socket.sendall)
- **C3** `wg_client_activator.py:WGClientActivation.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_client_activator.py:WGClientActivation.close` (socket.close)
- **C4** `handler:wg_client_API_handler.py:WGClientAPIHandler`
  - `wg_client_API_handler.py:WGClientAPIHandler.api_path` (http.server.path)
  - `wg_client_API_handler.py:WGClientAPIHandler.api_target` (http.server.path)
  - `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request` (http.server.command, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.do_CONNECT` (http.server.path, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE` (http.server.path, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.do_GET` (http.server.path, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.do_PATCH` (http.server.path, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.do_POST` (http.server.path)
  - `wg_client_API_handler.py:WGClientAPIHandler.do_PUT` (http.server.headers, http.server.path, http.server.rfile.read, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.principal_required` (http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.request_auth_headers` (http.server.headers)
  - `wg_client_API_handler.py:WGClientAPIHandler.send_error` (http.server.command, http.server.end_headers, http.server.path, http.server.send_header, http.server.send_response, http.server.wfile.write)
  - … +1
- **C5** `wg_client.py:systemd_notify.sock` — socket.AF_UNIX, socket.SOCK_DGRAM, socket.socket()
  - `wg_client.py:systemd_notify` (socket.<create socket.socket>, socket.close, socket.connect, socket.sendall)
- **C6** `wg_client_activator.py:activate_client.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_client_activator.py:activate_client` (socket.<create socket.socket>, socket.close, socket.connect, socket.makefile, socket.sendall)
- **C7** `wg_controller_client.py:WGClientClient._request.conn + wg_controller_client.py:WGClientClient._request.response` — 10, http.client, http.client.HTTPSConnection(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGClientClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getheader, http.client.getresponse, http.client.read, http.client.request)
- **C8** `wg_controller_client.py:WGControllerClient._request.conn + wg_controller_client.py:WGControllerClient._request.response` — 'ca', 'controller', 'host', 'port', 'timeout', 10, http.client, http.client.HTTPSConnection(), src.wg_client.wg_client_config.load_config(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGControllerClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getresponse, http.client.read, http.client.request)

## Forme dei messaggi (dict che arrivano ai sink)

- `{allowed_ip: ‹in http.server.rfile.read›('allowed_ip'|'utf-8'), public_key: ‹in http.server.path›('/v1/peers/')}` — `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:202, wg_controller_client.py:85
- `{}` — `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:304
- `{**: ‹wg_client_IPC.py:WGClientIPC.send_result(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, status: ‹wg_client_IPC.py:WGClientIPC.send_result(status)›∈{'ERROR'|'OK'}, type: 'A…` — `wg_client_IPC.py:WGClientIPC.send_result` — wg_client_IPC.py:245
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹in http.server.path›(','|'/v1/peers/'|'/v1/status'), <AUTH_MAC_HEADER>: 'mac' | ‹in http.server.path›(','|'/v1/peers/'|'/v1/status'), <AUTH_NONCE_HEADER>: 'nonce'…` — `wg_controller_client.py:WGClientClient._request` — wg_controller_client.py:129
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(code)›∈{400|401|403|404|405|502} | ‹wg_client_…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:312
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_json(code)›∈{200} | ‹in http.server.path,http.server…` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:312
- `{Accept: 'application/json', Connection: 'close', Content-Length: ‹wg_controller_client.py:WGControllerClient._request.data›∈{','|':'}, Content-Type: 'application/json'}` — `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:36
- `{client_id: ‹wg_client_activator.py:activate_client(client_id)›, created_at: ?, k_session: ‹wg_client_activator.py:activate_client(k_sess)›, listen_path: ‹wg_client_activator.py:activate_client(liste…` — `wg_client_activator.py:activate_client` — wg_client_activator.py:30
- `{error: ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(message)›∈{'Bad Request'|'Controller error'|'Forbidden'|'Unauthorized'}, message: ‹wg_client_API_handler.py:WGClientAPIHandler.send_err…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:349
- `{peers: 'peers' | ‹wg_client_API_handler.py:WGClientAPIHandler.do_GET.result›}` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:WGClientAPIHandler.filter_status_for_principal:filtered
- `{protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STOP'}` — `wg_client_IPC.py:WGClientIPC._notify_stop` — wg_client_IPC.py:258
- `{status: 'ok'}` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:462

## Cosa accettano i parametri (valori costanti che possono assumere)

- `wg_client.py:systemd_notify(message)` ∈ {'READY=1' | 'STATUS=session_id=' | 'STOPPING=1' | 'k_session' | 'listen_path' | 'principal' | 'session_id'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(explain)` ∈ {'Invalid peer request' | 'authenticated session has no principal' | 'controller interface mismatch' | 'invalid Content-Length' | 'invalid secure-session authentication' | 'peer is not owned by this principal' | 'secure-session authentication failed'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(code)` ∈ {400 | 401 | 403 | 404 | 405 | 502}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(message)` ∈ {'Bad Request' | 'Controller error' | 'Forbidden' | 'Unauthorized'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_json(obj)` ∈ {'/v1/peers/' | 'allowed_ip' | 'utf-8'}
- `wg_controller_client.py:WGClientClient._request(method)` ∈ {'DELETE' | 'GET' | 'PUT'}
- `wg_controller_client.py:WGControllerClient.__init__(timeout)` ∈ {'controller' | 'timeout' | 10}
- `wg_controller_client.py:WGControllerClient._request(method)` ∈ {'DELETE' | 'GET' | 'POST'}
- `wg_controller_client.py:WGControllerClient._request(path)` ∈ {'/v1/peers' | '/v1/peers/' | '/v1/status'}
- `wg_client_IPC.py:WGClientIPC.send_result(status)` ∈ {'ERROR' | 'OK'}
- `wg_controller_client.py:WGClientClient._request(path)` ∈ {'/v1/peers/' | '/v1/status'}
- `wg_controller_client.py:WGClientClient.add_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_controller_client.py:WGControllerClient.__init__(ca)` ∈ {'ca' | 'controller'}
- `wg_controller_client.py:WGControllerClient.__init__(host)` ∈ {'controller' | 'host'}
- `wg_controller_client.py:WGControllerClient.__init__(port)` ∈ {'controller' | 'port'}
- `wg_controller_client.py:WGControllerClient.add_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}

## Sink

### `wg_client.py:main` — socket.<create socket.socket>@L150
- via: os.dup, sys.stdin.fileno
- esterni: socket.AF_UNIX, socket.SOCK_STREAM, sys.stdin

### `wg_client.py:systemd_notify` — socket.<create socket.socket>@L45, socket.close@L52, socket.connect@L48, socket.sendall@L49
- via: .parse_activation, .parse_packet, .receive_packet, os.dup, os.environ.get, socket.socket, src.wg_client.wg_client_API.WGClientAPI, src.wg_client.wg_client_IPC.WGClientIPC, src.wg_client.wg_client_config.load_config, src.wg_client.wg_client_lifecycle.WGClientLifecycle, src.wg_client.wg_secure_session.WGSecureSession, sys.stdin.fileno
- costanti dirette: 'NOTIFY_SOCKET', 'READY=1', 'STATUS=session_id=', 'STOPPING=1', '\x00', 'k_session', 'listen_path', 'principal', 'session_id', 1
- esterni: os.environ, socket.AF_UNIX, socket.SOCK_DGRAM, socket.SOCK_STREAM, sys.stdin

### `wg_client_API_handler.py:WGClientAPIHandler.api_path` — http.server.path@L170

### `wg_client_API_handler.py:WGClientAPIHandler.api_target` — http.server.path@L189

### `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request` — http.server.command@L279, http.server.send_error@L271, http.server.send_error@L283, http.server.send_error@L288
- costanti dirette: 'Bad Request', 'Unauthorized', 'invalid secure-session authentication', 'secure-session authentication failed', 400, 401, 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_CONNECT` — http.server.path@L505, http.server.send_error@L506
- costanti dirette: 405

### `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE` — http.server.path@L465, http.server.send_error@L474, http.server.send_error@L481, http.server.send_error@L492
- costanti dirette: 'Controller error', 'Forbidden', 'peer is not owned by this principal', 403, 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_GET` — http.server.path@L417, http.server.send_error@L424, http.server.send_error@L434, http.server.send_error@L443
- costanti dirette: 'Controller error', 'controller interface mismatch', 404, 502

### `wg_client_API_handler.py:WGClientAPIHandler.do_PATCH` — http.server.path@L509, http.server.send_error@L510
- costanti dirette: 405

### `wg_client_API_handler.py:WGClientAPIHandler.do_POST` — http.server.path@L456

### `wg_client_API_handler.py:WGClientAPIHandler.do_PUT` — http.server.headers@L516, http.server.path@L513, http.server.rfile.read@L522, http.server.send_error@L525, http.server.send_error@L537, http.server.send_error@L548
- costanti dirette: 'Bad Request', 'Content-Length', 'Controller error', 'Forbidden', 'Invalid peer request', 'controller interface mismatch', 'invalid Content-Length', 'peer is not owned by this principal', 0, 400, 403, 404 (+1)
- dalla rete: http.server.headers

### `wg_client_API_handler.py:WGClientAPIHandler.principal_required` — http.server.send_error@L127
- costanti dirette: 'Forbidden', 'authenticated session has no principal', 403

### `wg_client_API_handler.py:WGClientAPIHandler.request_auth_headers` — http.server.headers@L228, http.server.headers@L229, http.server.headers@L230, http.server.headers@L231

### `wg_client_API_handler.py:WGClientAPIHandler.send_error` — http.server.command@L379, http.server.end_headers@L377, http.server.path@L354, http.server.send_header@L368, http.server.send_header@L371, http.server.send_header@L374
- via: json.dumps
- costanti dirette: 'Bad Request', 'Connection', 'Content-Length', 'Content-Type', 'Controller error', 'Forbidden', 'Unauthorized', 'application/json', 'close', 'utf-8', 400, 401 (+4)
- forme: 3 (vedi sopra)

### `wg_client_API_handler.py:WGClientAPIHandler.send_json` — http.server.command@L396, http.server.end_headers@L394, http.server.send_header@L390, http.server.send_header@L392, http.server.send_header@L393, http.server.send_response@L387
- via: .add_peer, .remove_peer, .status, json.dumps, json.loads, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: '/v1/peers/', 'Content-Length', 'Content-Type', 'allowed_ip', 'application/json', 'utf-8', 200
- dalla rete: http.server.path, http.server.rfile.read
- forme: 4 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._notify_stop` — socket.sendall@L262
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC.receive_packet` — socket.recv@L85
- costanti dirette: 4096

### `wg_client_IPC.py:WGClientIPC.send_result` — socket.sendall@L252
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_activator.py:WGClientActivation.close` — socket.close@L12

### `wg_client_activator.py:activate_client` — socket.<create socket.socket>@L48, socket.close@L79, socket.connect@L54, socket.makefile@L57, socket.sendall@L55
- via: json.dumps
- costanti dirette: ',', ':', '\n', 'rb', 'utf-8'
- esterni: socket.AF_UNIX, socket.SOCK_STREAM
- input aperti alle radici: input wg_client_activator.py:activate_client(socket_path)
- forme: 1 (vedi sopra)

### `wg_controller_client.py:WGClientClient._request` — http.client.<create http.client.HTTPSConnection>@L126, http.client.close@L191, http.client.getheader@L170, http.client.getheader@L171, http.client.getheader@L172, http.client.getresponse@L160
- via: json.dumps, ssl.create_default_context, urllib.parse.quote, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: ',', '/v1/peers/', '/v1/status', ':', 'DELETE', 'GET', 'PUT', 10
- esterni: src.wg_client.wg_client_API_handler.AUTH_COUNTER_HEADER, src.wg_client.wg_client_API_handler.AUTH_MAC_HEADER, src.wg_client.wg_client_API_handler.AUTH_SESSION_ID_HEADER, ssl.Purpose.SERVER_AUTH
- dalla rete: http.server.path
- input aperti alle radici: input wg_controller_client.py:WGClientClient.__init__(ca), input wg_controller_client.py:WGClientClient.__init__(host), input wg_controller_client.py:WGClientClient.__init__(listen_path), input wg_controller_client.py:WGClientClient.__init__(port), input wg_controller_client.py:WGClientClient.__init__(timeout)
- forme: 2 (vedi sopra)

### `wg_controller_client.py:WGControllerClient._request` — http.client.<create http.client.HTTPSConnection>@L32, http.client.close@L74, http.client.getresponse@L49, http.client.read@L50, http.client.request@L47
- via: json.dumps, src.wg_client.wg_client_config.load_config, ssl.create_default_context, urllib.parse.quote, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: ',', '/v1/peers', '/v1/peers/', '/v1/status', ':', 'DELETE', 'GET', 'POST', 'ca', 'controller', 'host', 'port' (+2)
- esterni: ssl.Purpose.SERVER_AUTH
- dalla rete: http.server.path
- forme: 2 (vedi sopra)

## Intersezioni (nodi condivisi da piu' sink)

- var `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE.public_key` → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.allowed_ip` → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.public_key` → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- attr `wg_client_API_handler.py:WGClientAPIHandler.request_auth` → 2 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- var `wg_client_IPC.py:PROTOCOL_VERSION` → 2 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC.send_result`

### Valori condivisi

- const 'utf-8' → 7 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC.send_result`
- const ',' → 5 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC.send_result`, `wg_client_activator.py:activate_client`, `wg_controller_client.py:WGClientClient._request`
- const ':' → 5 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC.send_result`, `wg_client_activator.py:activate_client`, `wg_controller_client.py:WGClientClient._request`
- const 404 → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`
- const 'Controller error' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'Forbidden' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.principal_required`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'application/json' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 'session_id' → 4 sink: `wg_client.py:systemd_notify`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 1 → 4 sink: `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC.send_result`, `wg_client_activator.py:activate_client`
- const 403 → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.principal_required`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- in http.server.path → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- ext socket.AF_UNIX → 4 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.send_result`, `wg_client_activator.py:activate_client`
- ext socket.SOCK_STREAM → 4 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.send_result`, `wg_client_activator.py:activate_client`
- const 'Bad Request' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'Content-Length' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- const 'close' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 'controller interface mismatch' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'counter' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 'mac' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 'peer is not owned by this principal' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 400 → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 405 → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_CONNECT`, `wg_client_API_handler.py:WGClientAPIHandler.do_PATCH`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 502 → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- in http.server.headers → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- … +15

