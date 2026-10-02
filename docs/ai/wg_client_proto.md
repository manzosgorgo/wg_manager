# Snapshot del protocollo (passo 2)

- Sink analizzati: 24
- Nodi: attr=14, const=71, ext=12, in=4, open=13, param=58, shape=21, sink=24, var=68, xf=29 · archi: 479

## Canali (sink con lo stesso ricevente)

- **C1** `<senza ricevente>`
  - `wg_client.py:main` (socket.<create socket.socket>)
- **C2** `wg_client_IPC.py:WGClientIPC.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._notify_stop` (socket.sendall)
  - `wg_client_IPC.py:WGClientIPC.receive_packet` (socket.recv)
  - `wg_client_IPC.py:WGClientIPC.reconcile_state` (socket.sendall)
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
  - `wg_client_API_handler.py:WGClientAPIHandler.request_auth_headers` (http.server.headers)
  - `wg_client_API_handler.py:WGClientAPIHandler.send_error` (http.server.command, http.server.end_headers, http.server.path, http.server.send_header, http.server.send_response, http.server.wfile.write)
  - `wg_client_API_handler.py:WGClientAPIHandler.send_json` (http.server.command, http.server.end_headers, http.server.send_header, http.server.send_response, http.server.wfile.write)
- **C5** `wg_client.py:systemd_notify.sock` — socket.AF_UNIX, socket.SOCK_DGRAM, socket.socket()
  - `wg_client.py:systemd_notify` (socket.<create socket.socket>, socket.close, socket.connect, socket.sendall)
- **C6** `wg_client_IPC.py:WGClientIPC._ownership_request.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._ownership_request` (socket.sendall)
- **C7** `wg_client_IPC.py:WGClientIPC._peer_request.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._peer_request` (socket.sendall)
- **C8** `wg_client_activator.py:activate_client.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_client_activator.py:activate_client` (socket.<create socket.socket>, socket.close, socket.connect, socket.makefile, socket.sendall)
- **C9** `wg_controller_client.py:WGClientClient._request.conn + wg_controller_client.py:WGClientClient._request.response` — 10, http.client, http.client.HTTPSConnection(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGClientClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getheader, http.client.getresponse, http.client.read, http.client.request)
- **C10** `wg_controller_client.py:WGControllerClient._request.conn + wg_controller_client.py:WGControllerClient._request.response` — 'ca', 'controller', 'host', 'port', 'timeout', 10, http.client, http.client.HTTPSConnection(), src.wg_client.wg_client_config.load_config(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGControllerClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getresponse, http.client.read, http.client.request)

## Forme dei messaggi (dict che arrivano ai sink)

- `{allowed_ip: ‹in http.server.rfile.read›('allowed_ip'|'utf-8'), public_key: ‹in http.server.path›('/v1/peers/')}` — `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:202, wg_controller_client.py:85
- `{}` — `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:277
- `{**: ‹wg_client_IPC.py:WGClientIPC._ownership_request(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_client_IPC.py:WGClientIPC._ownership_request.request_id›∈{1}…` — `wg_client_IPC.py:WGClientIPC._ownership_request` — wg_client_IPC.py:369
- `{**: ‹wg_client_IPC.py:WGClientIPC.send_result(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, status: ‹wg_client_IPC.py:WGClientIPC.send_result(status)›∈{'ERROR'|'OK'}, type: 'A…` — `wg_client_IPC.py:WGClientIPC.send_result` — wg_client_IPC.py:486
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹in http.server.path›(','|'/v1/peers/'|'/v1/status'), <AUTH_MAC_HEADER>: 'mac' | ‹in http.server.path›(','|'/v1/peers/'|'/v1/status'), <AUTH_NONCE_HEADER>: 'nonce'…` — `wg_controller_client.py:WGClientClient._request` — wg_controller_client.py:129
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(code)›∈{400|401|404|405} | ‹wg_client_API_hand…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:285
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_json(code)›∈{200} | ‹in http.server.path,http.server…` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:285
- `{Accept: 'application/json', Connection: 'close', Content-Length: ‹wg_controller_client.py:WGControllerClient._request.data›∈{','|':'}, Content-Type: 'application/json'}` — `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:36
- `{allowed_ip: ‹in http.server.rfile.read›('allowed_ip'|'utf-8'), protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, public_key: ‹in http.server.path›('/v1/peers/'), request_id: ‹wg_client_IPC.…` — `wg_client_IPC.py:WGClientIPC._peer_request` — wg_client_IPC.py:288
- `{client_id: ‹wg_client_activator.py:activate_client(client_id)›, created_at: ?, k_session: ‹wg_client_activator.py:activate_client(k_sess)›, listen_path: ‹wg_client_activator.py:activate_client(liste…` — `wg_client_activator.py:activate_client` — wg_client_activator.py:30
- `{error: ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(message)›∈{'Bad Request'|'Peer service error'|'Unauthorized'}, message: ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(explain…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:322
- `{peers: ‹wg_client_IPC.py:WGClientIPC.reconcile_state(peers)›∈{'k_session'|'listen_path'|'principal'|'session_id'}, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STATE_SNAPSHOT'}` — `wg_client_IPC.py:WGClientIPC.reconcile_state` — wg_client_IPC.py:441
- `{protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STOP'}` — `wg_client_IPC.py:WGClientIPC._notify_stop` — wg_client_IPC.py:500
- `{status: 'ok'}` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:424

## Cosa accettano i parametri (valori costanti che possono assumere)

- `wg_client.py:systemd_notify(message)` ∈ {'READY=1' | 'STATUS=session_id=' | 'STOPPING=1' | 'k_session' | 'listen_path' | 'principal' | 'session_id'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_json(obj)` ∈ {'/owner' | '/v1/admin/peers/' | '/v1/peers/' | 'allowed_ip' | 'username' | 'utf-8'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(explain)` ∈ {'Invalid ownership request' | 'Invalid peer request' | 'invalid Content-Length' | 'invalid secure-session authentication' | 'secure-session authentication failed'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(code)` ∈ {400 | 401 | 404 | 405}
- `wg_client_IPC.py:WGClientIPC.reconcile_state(peers)` ∈ {'k_session' | 'listen_path' | 'principal' | 'session_id'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(message)` ∈ {'Bad Request' | 'Peer service error' | 'Unauthorized'}
- `wg_controller_client.py:WGClientClient._request(method)` ∈ {'DELETE' | 'GET' | 'PUT'}
- `wg_controller_client.py:WGControllerClient.__init__(timeout)` ∈ {'controller' | 'timeout' | 10}
- `wg_controller_client.py:WGControllerClient._request(method)` ∈ {'DELETE' | 'GET' | 'POST'}
- `wg_controller_client.py:WGControllerClient._request(path)` ∈ {'/v1/peers' | '/v1/peers/' | '/v1/status'}
- `wg_client_IPC.py:WGClientIPC._ownership_request(command)` ∈ {'OWNERSHIP_REASSIGN' | 'OWNERSHIP_STATE'}
- `wg_client_IPC.py:WGClientIPC._peer_request(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC._peer_request(command)` ∈ {'PEER_REGISTER' | 'PEER_UNREGISTER'}
- `wg_client_IPC.py:WGClientIPC.reassign_owner(public_key)` ∈ {'/owner' | '/v1/admin/peers/'}
- `wg_client_IPC.py:WGClientIPC.reassign_owner(username)` ∈ {'username' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC.register_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC.send_result(status)` ∈ {'ERROR' | 'OK'}
- `wg_controller_client.py:WGClientClient._request(path)` ∈ {'/v1/peers/' | '/v1/status'}
- `wg_controller_client.py:WGClientClient.add_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_controller_client.py:WGControllerClient.__init__(ca)` ∈ {'ca' | 'controller'}
- `wg_controller_client.py:WGControllerClient.__init__(host)` ∈ {'controller' | 'host'}
- `wg_controller_client.py:WGControllerClient.__init__(port)` ∈ {'controller' | 'port'}
- `wg_controller_client.py:WGControllerClient.add_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_peer_service.py:WGPeerService.add_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- … +2

## Sink

### `wg_client.py:main` — socket.<create socket.socket>@L193
- via: os.dup, sys.stdin.fileno
- esterni: socket.AF_UNIX, socket.SOCK_STREAM, sys.stdin

### `wg_client.py:systemd_notify` — socket.<create socket.socket>@L45, socket.close@L52, socket.connect@L48, socket.sendall@L49
- via: .parse_activation, .parse_packet, .receive_packet, os.dup, os.environ.get, socket.socket, src.wg_client.wg_client_API.WGClientAPI, src.wg_client.wg_client_IPC.WGClientIPC, src.wg_client.wg_client_config.load_config, src.wg_client.wg_client_lifecycle.WGClientLifecycle, src.wg_client.wg_secure_session.WGSecureSession, sys.stdin.fileno
- costanti dirette: 'NOTIFY_SOCKET', 'READY=1', 'STATUS=session_id=', 'STOPPING=1', '\x00', 'k_session', 'listen_path', 'principal', 'session_id', 1
- esterni: os.environ, socket.AF_UNIX, socket.SOCK_DGRAM, socket.SOCK_STREAM, sys.stdin

### `wg_client_API_handler.py:WGClientAPIHandler.api_path` — http.server.path@L133

### `wg_client_API_handler.py:WGClientAPIHandler.api_target` — http.server.path@L152

### `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request` — http.server.command@L252, http.server.send_error@L247, http.server.send_error@L256, http.server.send_error@L261
- costanti dirette: 'Bad Request', 'Unauthorized', 'invalid secure-session authentication', 'secure-session authentication failed', 400, 401, 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_CONNECT` — http.server.path@L451, http.server.send_error@L452
- costanti dirette: 405

### `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE` — http.server.path@L427, http.server.send_error@L435, http.server.send_error@L441
- costanti dirette: 'Peer service error', 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_GET` — http.server.path@L390, http.server.send_error@L404, http.server.send_error@L408
- costanti dirette: 'Peer service error', 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_PATCH` — http.server.path@L455, http.server.send_error@L456
- costanti dirette: 405

### `wg_client_API_handler.py:WGClientAPIHandler.do_POST` — http.server.path@L418

### `wg_client_API_handler.py:WGClientAPIHandler.do_PUT` — http.server.headers@L462, http.server.path@L459, http.server.rfile.read@L465, http.server.send_error@L467, http.server.send_error@L497, http.server.send_error@L505
- costanti dirette: 'Bad Request', 'Content-Length', 'Invalid ownership request', 'Invalid peer request', 'Peer service error', 'invalid Content-Length', 0, 400, 404
- dalla rete: http.server.headers

### `wg_client_API_handler.py:WGClientAPIHandler.request_auth_headers` — http.server.headers@L206, http.server.headers@L207, http.server.headers@L208, http.server.headers@L209

### `wg_client_API_handler.py:WGClientAPIHandler.send_error` — http.server.command@L352, http.server.end_headers@L350, http.server.path@L327, http.server.send_header@L341, http.server.send_header@L344, http.server.send_header@L347
- via: json.dumps
- costanti dirette: 'Bad Request', 'Connection', 'Content-Length', 'Content-Type', 'Peer service error', 'Unauthorized', 'application/json', 'close', 'utf-8', 400, 401, 404 (+1)
- forme: 3 (vedi sopra)

### `wg_client_API_handler.py:WGClientAPIHandler.send_json` — http.server.command@L369, http.server.end_headers@L367, http.server.send_header@L363, http.server.send_header@L365, http.server.send_header@L366, http.server.send_response@L360
- via: .add_peer, .admin_status, .reassign_owner, .remove_peer, .status, json.dumps, json.loads, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: '/owner', '/v1/admin/peers/', '/v1/peers/', 'Content-Length', 'Content-Type', 'allowed_ip', 'application/json', 'username', 'utf-8', 200
- dalla rete: http.server.path, http.server.rfile.read
- forme: 3 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._notify_stop` — socket.sendall@L505
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._ownership_request` — socket.sendall@L382
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._peer_request` — socket.sendall@L305
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC.receive_packet` — socket.recv@L97
- costanti dirette: 4096

### `wg_client_IPC.py:WGClientIPC.reconcile_state` — socket.sendall@L449
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC.send_result` — socket.sendall@L494
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

- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.obj` → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.path` → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- var `wg_client_IPC.py:PROTOCOL_VERSION` → 5 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE.public_key` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.allowed_ip` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.public_key` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client.py:activate.activation` → 2 sink: `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- var `wg_client.py:activate.cfg` → 2 sink: `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.admin_public_key` → 2 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.username` → 2 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- attr `wg_client_API_handler.py:WGClientAPIHandler.request_auth` → 2 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- attr `wg_client_IPC.py:WGClientIPC._next_request_id` → 2 sink: `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`

### Valori condivisi

- const 'utf-8' → 10 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const ',' → 8 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- const ':' → 8 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- const 1 → 7 sink: `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- in http.server.path → 6 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- const 'session_id' → 5 sink: `wg_client.py:systemd_notify`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- const 404 → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`
- const b'\n' → 5 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- ext socket.AF_UNIX → 5 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- ext socket.SOCK_STREAM → 5 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- const 'Peer service error' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'application/json' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- ext sys.stdin → 4 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- const 'Bad Request' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'Content-Length' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- const 'close' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 'counter' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 'mac' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 400 → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 405 → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_CONNECT`, `wg_client_API_handler.py:WGClientAPIHandler.do_PATCH`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- in http.server.headers → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- const '/v1/status' → 2 sink: `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 'Content-Type' → 2 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- const 'DELETE' → 2 sink: `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- … +13

