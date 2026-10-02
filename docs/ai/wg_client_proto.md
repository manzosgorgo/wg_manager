# Snapshot del protocollo (passo 2)

- Sink analizzati: 27
- Nodi: attr=14, const=81, ext=12, in=4, open=13, param=66, shape=28, sink=27, var=85, xf=32 · archi: 577

## Canali (sink con lo stesso ricevente)

- **C1** `<senza ricevente>`
  - `wg_client.py:main` (socket.<create socket.socket>)
- **C2** `wg_client_IPC.py:WGClientIPC.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._notify_stop` (socket.sendall)
  - `wg_client_IPC.py:WGClientIPC.provisioning_state` (socket.sendall)
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
  - `wg_client_API_handler.py:WGClientAPIHandler.do_POST` (http.server.headers, http.server.path, http.server.rfile.read, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.do_PUT` (http.server.headers, http.server.path, http.server.rfile.read, http.server.send_error)
  - `wg_client_API_handler.py:WGClientAPIHandler.request_auth_headers` (http.server.headers)
  - `wg_client_API_handler.py:WGClientAPIHandler.send_error` (http.server.command, http.server.end_headers, http.server.path, http.server.send_header, http.server.send_response, http.server.wfile.write)
  - `wg_client_API_handler.py:WGClientAPIHandler.send_json` (http.server.command, http.server.end_headers, http.server.send_header, http.server.send_response, http.server.wfile.write)
- **C5** `wg_client.py:systemd_notify.sock` — socket.AF_UNIX, socket.SOCK_DGRAM, socket.socket()
  - `wg_client.py:systemd_notify` (socket.<create socket.socket>, socket.close, socket.connect, socket.sendall)
- **C6** `wg_client_IPC.py:WGClientIPC._account_request.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._account_request` (socket.sendall)
- **C7** `wg_client_IPC.py:WGClientIPC._ownership_request.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._ownership_request` (socket.sendall)
- **C8** `wg_client_IPC.py:WGClientIPC._peer_request.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._peer_request` (socket.sendall)
- **C9** `wg_client_IPC.py:WGClientIPC.keepalive.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC.keepalive` (socket.sendall)
- **C10** `wg_client_activator.py:activate_client.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_client_activator.py:activate_client` (socket.<create socket.socket>, socket.close, socket.connect, socket.makefile, socket.sendall)
- **C11** `wg_controller_client.py:WGClientClient._request.conn + wg_controller_client.py:WGClientClient._request.response` — 10, http.client, http.client.HTTPSConnection(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGClientClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getheader, http.client.getresponse, http.client.read, http.client.request)
- **C12** `wg_controller_client.py:WGControllerClient._request.conn + wg_controller_client.py:WGControllerClient._request.response` — 'ca', 'controller', 'host', 'port', 'timeout', 10, http.client, http.client.HTTPSConnection(), src.wg_client.wg_client_config.load_config(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGControllerClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getresponse, http.client.read, http.client.request)

## Forme dei messaggi (dict che arrivano ai sink)

- `{allowed_ip: ‹in http.server.rfile.read›('allowed_ip'|'utf-8'), public_key: ‹in http.server.path›('/v1/peers/')}` — `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:206, wg_controller_client.py:89
- `{}` — `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:328
- `{**: ‹wg_client_IPC.py:WGClientIPC._account_request(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_client_IPC.py:WGClientIPC._account_request.request_id›∈{1}, ty…` — `wg_client_IPC.py:WGClientIPC._account_request` — wg_client_IPC.py:508
- `{**: ‹wg_client_IPC.py:WGClientIPC._ownership_request(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_client_IPC.py:WGClientIPC._ownership_request.request_id›∈{1}…` — `wg_client_IPC.py:WGClientIPC._ownership_request` — wg_client_IPC.py:375
- `{**: ‹wg_client_IPC.py:WGClientIPC.send_result(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, status: ‹wg_client_IPC.py:WGClientIPC.send_result(status)›∈{'ERROR'|'OK'}, type: 'A…` — `wg_client_IPC.py:WGClientIPC.send_result` — wg_client_IPC.py:621
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹in http.server.path›(','|'/v1/peers/'|'/v1/status'), <AUTH_MAC_HEADER>: 'mac' | ‹in http.server.path›(','|'/v1/peers/'|'/v1/status'), <AUTH_NONCE_HEADER>: 'nonce'…` — `wg_controller_client.py:WGClientClient._request` — wg_controller_client.py:133
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(code)›∈{400|401|404|405} | ‹wg_client_API_hand…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:336
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_json(code)›∈{200|201} | ‹in http.server.path,http.se…` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:336
- `{Accept: 'application/json', Connection: 'close', Content-Length: ‹wg_controller_client.py:WGControllerClient._request.data›∈{','|':'}, Content-Type: 'application/json'}` — `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:36
- `{allowed_ip: ‹in http.server.rfile.read›('allowed_ip'|'utf-8'), protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, public_key: ‹in http.server.path›('/v1/peers/'), request_id: ‹wg_client_IPC.…` — `wg_client_IPC.py:WGClientIPC._peer_request` — wg_client_IPC.py:294
- `{client_id: ‹wg_client_activator.py:activate_client(client_id)›, created_at: ?, k_session: ‹wg_client_activator.py:activate_client(k_sess)›, listen_path: ‹wg_client_activator.py:activate_client(liste…` — `wg_client_activator.py:activate_client` — wg_client_activator.py:31
- `{error: ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(message)›∈{'Bad Request'|'Peer service error'|'Unauthorized'}, message: ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(explain…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:373
- `{ok: True}` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:453, wg_client_API_handler.py:548
- `{peers: ‹wg_client_IPC.py:WGClientIPC.reconcile_state(peers)›∈{'k_session'|'listen_path'|'principal'|'session_id'}, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STATE_SNAPSHOT'}` — `wg_client_IPC.py:WGClientIPC.reconcile_state` — wg_client_IPC.py:576
- `{protocol_version: 1, status: 'OK', type: 'STATE_RESULT'}` — `wg_client_activator.py:activate_client` — wg_client_activator.py:90
- `{protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_client_IPC.py:WGClientIPC.provisioning_state.request_id›∈{1}, type: 'PROVISIONING_STATE'}` — `wg_client_IPC.py:WGClientIPC.provisioning_state` — wg_client_IPC.py:440
- `{protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'KEEPALIVE'}` — `wg_client_IPC.py:WGClientIPC.keepalive` — wg_client_IPC.py:636
- `{protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STOP'}` — `wg_client_IPC.py:WGClientIPC._notify_stop` — wg_client_IPC.py:653

## Cosa accettano i parametri (valori costanti che possono assumere)

- `wg_client_API_handler.py:WGClientAPIHandler.send_json(obj)` ∈ {'/owner' | '/v1/admin/peers/' | '/v1/admin/users/' | '/v1/peers/' | 'allowed_ip' | 'password' | 'username' | 'utf-8'}
- `wg_client.py:systemd_notify(message)` ∈ {'READY=1' | 'STATUS=session_id=' | 'STOPPING=1' | 'k_session' | 'listen_path' | 'principal' | 'session_id'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(explain)` ∈ {'Invalid account request' | 'Invalid ownership request' | 'Invalid peer request' | 'invalid Content-Length' | 'invalid secure-session authentication' | 'secure-session authentication failed'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(code)` ∈ {400 | 401 | 404 | 405}
- `wg_client_IPC.py:WGClientIPC.reconcile_state(peers)` ∈ {'k_session' | 'listen_path' | 'principal' | 'session_id'}
- `wg_controller_client.py:WGControllerClient._request(path)` ∈ {'/v1/peers' | '/v1/peers/' | '/v1/provisioning' | '/v1/status'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(message)` ∈ {'Bad Request' | 'Peer service error' | 'Unauthorized'}
- `wg_controller_client.py:WGClientClient._request(method)` ∈ {'DELETE' | 'GET' | 'PUT'}
- `wg_controller_client.py:WGControllerClient.__init__(timeout)` ∈ {'controller' | 'timeout' | 10}
- `wg_controller_client.py:WGControllerClient._request(method)` ∈ {'DELETE' | 'GET' | 'POST'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_json(code)` ∈ {200 | 201}
- `wg_client_IPC.py:WGClientIPC._account_request(command)` ∈ {'ACCOUNT_CREATE' | 'ACCOUNT_DELETE'}
- `wg_client_IPC.py:WGClientIPC._ownership_request(command)` ∈ {'OWNERSHIP_REASSIGN' | 'OWNERSHIP_STATE'}
- `wg_client_IPC.py:WGClientIPC._peer_request(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC._peer_request(command)` ∈ {'PEER_REGISTER' | 'PEER_UNREGISTER'}
- `wg_client_IPC.py:WGClientIPC.create_user(password)` ∈ {'password' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC.create_user(username)` ∈ {'username' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC.reassign_owner(public_key)` ∈ {'/owner' | '/v1/admin/peers/'}
- `wg_client_IPC.py:WGClientIPC.reassign_owner(username)` ∈ {'username' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC.register_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC.send_result(status)` ∈ {'ERROR' | 'OK'}
- `wg_controller_client.py:WGClientClient._request(path)` ∈ {'/v1/peers/' | '/v1/status'}
- `wg_controller_client.py:WGClientClient.add_peer(allowed_ip)` ∈ {'allowed_ip' | 'utf-8'}
- `wg_controller_client.py:WGControllerClient.__init__(ca)` ∈ {'ca' | 'controller'}
- … +8

## Sink

### `wg_client.py:main` — socket.<create socket.socket>@L193
- via: os.dup, sys.stdin.fileno
- esterni: socket.AF_UNIX, socket.SOCK_STREAM, sys.stdin

### `wg_client.py:systemd_notify` — socket.<create socket.socket>@L45, socket.close@L52, socket.connect@L48, socket.sendall@L49
- via: .parse_activation, .parse_packet, .receive_packet, os.dup, os.environ.get, socket.socket, src.wg_client.wg_client_API.WGClientAPI, src.wg_client.wg_client_IPC.WGClientIPC, src.wg_client.wg_client_config.load_config, src.wg_client.wg_client_lifecycle.WGClientLifecycle, src.wg_client.wg_secure_session.WGSecureSession, sys.stdin.fileno
- costanti dirette: 'NOTIFY_SOCKET', 'READY=1', 'STATUS=session_id=', 'STOPPING=1', '\x00', 'k_session', 'listen_path', 'principal', 'session_id', 1
- esterni: os.environ, socket.AF_UNIX, socket.SOCK_DGRAM, socket.SOCK_STREAM, sys.stdin

### `wg_client_API_handler.py:WGClientAPIHandler.api_path` — http.server.path@L140

### `wg_client_API_handler.py:WGClientAPIHandler.api_target` — http.server.path@L172

### `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request` — http.server.command@L298, http.server.send_error@L293, http.server.send_error@L302, http.server.send_error@L307
- costanti dirette: 'Bad Request', 'Unauthorized', 'invalid secure-session authentication', 'secure-session authentication failed', 400, 401, 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_CONNECT` — http.server.path@L589, http.server.send_error@L590
- costanti dirette: 405

### `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE` — http.server.path@L539, http.server.send_error@L555, http.server.send_error@L561, http.server.send_error@L573, http.server.send_error@L579
- costanti dirette: 'Peer service error', 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_GET` — http.server.path@L441, http.server.send_error@L468, http.server.send_error@L472
- costanti dirette: 'Peer service error', 404

### `wg_client_API_handler.py:WGClientAPIHandler.do_PATCH` — http.server.path@L593, http.server.send_error@L594
- costanti dirette: 405

### `wg_client_API_handler.py:WGClientAPIHandler.do_POST` — http.server.headers@L485, http.server.path@L482, http.server.rfile.read@L488, http.server.send_error@L490, http.server.send_error@L498, http.server.send_error@L522
- costanti dirette: 'Bad Request', 'Content-Length', 'Invalid account request', 'Peer service error', 'invalid Content-Length', 0, 400, 404
- dalla rete: http.server.headers

### `wg_client_API_handler.py:WGClientAPIHandler.do_PUT` — http.server.headers@L600, http.server.path@L597, http.server.rfile.read@L603, http.server.send_error@L605, http.server.send_error@L635, http.server.send_error@L643
- costanti dirette: 'Bad Request', 'Content-Length', 'Invalid ownership request', 'Invalid peer request', 'Peer service error', 'invalid Content-Length', 0, 400, 404
- dalla rete: http.server.headers

### `wg_client_API_handler.py:WGClientAPIHandler.request_auth_headers` — http.server.headers@L252, http.server.headers@L253, http.server.headers@L254, http.server.headers@L255

### `wg_client_API_handler.py:WGClientAPIHandler.send_error` — http.server.command@L403, http.server.end_headers@L401, http.server.path@L378, http.server.send_header@L392, http.server.send_header@L395, http.server.send_header@L398
- via: json.dumps
- costanti dirette: 'Bad Request', 'Connection', 'Content-Length', 'Content-Type', 'Peer service error', 'Unauthorized', 'application/json', 'close', 'utf-8', 400, 401, 404 (+1)
- forme: 3 (vedi sopra)

### `wg_client_API_handler.py:WGClientAPIHandler.send_json` — http.server.command@L420, http.server.end_headers@L418, http.server.send_header@L414, http.server.send_header@L416, http.server.send_header@L417, http.server.send_response@L411
- via: .add_peer, .admin_status, .create_user, .delete_user, .provisioning, .reassign_owner, .remove_peer, .status, json.dumps, json.loads, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: '/owner', '/v1/admin/peers/', '/v1/admin/users/', '/v1/peers/', 'Content-Length', 'Content-Type', 'allowed_ip', 'application/json', 'password', 'username', 'utf-8', 200 (+1)
- dalla rete: http.server.path, http.server.rfile.read
- forme: 4 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._account_request` — socket.sendall@L521
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._notify_stop` — socket.sendall@L658
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._ownership_request` — socket.sendall@L388
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC._peer_request` — socket.sendall@L311
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC.keepalive` — socket.sendall@L643
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC.provisioning_state` — socket.sendall@L448
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC.receive_packet` — socket.recv@L109
- costanti dirette: 4096

### `wg_client_IPC.py:WGClientIPC.reconcile_state` — socket.sendall@L584
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_IPC.py:WGClientIPC.send_result` — socket.sendall@L629
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 1 (vedi sopra)

### `wg_client_activator.py:WGClientActivation.close` — socket.close@L12

### `wg_client_activator.py:activate_client` — socket.<create socket.socket>@L49, socket.close@L116, socket.connect@L55, socket.makefile@L57, socket.sendall@L56, socket.sendall@L96
- via: json.dumps
- costanti dirette: ',', ':', '\n', 'rb', 'utf-8'
- esterni: socket.AF_UNIX, socket.SOCK_STREAM
- input aperti alle radici: input wg_client_activator.py:activate_client(socket_path)
- forme: 2 (vedi sopra)

### `wg_controller_client.py:WGClientClient._request` — http.client.<create http.client.HTTPSConnection>@L130, http.client.close@L195, http.client.getheader@L174, http.client.getheader@L175, http.client.getheader@L176, http.client.getresponse@L164
- via: json.dumps, ssl.create_default_context, urllib.parse.quote, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: ',', '/v1/peers/', '/v1/status', ':', 'DELETE', 'GET', 'PUT', 10
- esterni: src.wg_client.wg_client_API_handler.AUTH_COUNTER_HEADER, src.wg_client.wg_client_API_handler.AUTH_MAC_HEADER, src.wg_client.wg_client_API_handler.AUTH_SESSION_ID_HEADER, ssl.Purpose.SERVER_AUTH
- dalla rete: http.server.path
- input aperti alle radici: input wg_controller_client.py:WGClientClient.__init__(ca), input wg_controller_client.py:WGClientClient.__init__(host), input wg_controller_client.py:WGClientClient.__init__(listen_path), input wg_controller_client.py:WGClientClient.__init__(port), input wg_controller_client.py:WGClientClient.__init__(timeout)
- forme: 2 (vedi sopra)

### `wg_controller_client.py:WGControllerClient._request` — http.client.<create http.client.HTTPSConnection>@L32, http.client.close@L74, http.client.getresponse@L49, http.client.read@L50, http.client.request@L47
- via: json.dumps, src.wg_client.wg_client_config.load_config, ssl.create_default_context, urllib.parse.quote, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: ',', '/v1/peers', '/v1/peers/', '/v1/provisioning', '/v1/status', ':', 'DELETE', 'GET', 'POST', 'ca', 'controller', 'host' (+3)
- esterni: ssl.Purpose.SERVER_AUTH
- dalla rete: http.server.path
- forme: 2 (vedi sopra)

## Intersezioni (nodi condivisi da piu' sink)

- var `wg_client_IPC.py:PROTOCOL_VERSION` → 8 sink: `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE.path` → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.obj` → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.path` → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE.public_key` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.allowed_ip` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.public_key` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- attr `wg_client_IPC.py:WGClientIPC._next_request_id` → 4 sink: `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_client_IPC.py:WGClientIPC.provisioning_state`
- var `wg_client.py:activate.activation` → 2 sink: `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- var `wg_client.py:activate.cfg` → 2 sink: `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE.username` → 2 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._account_request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_POST.password` → 2 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._account_request`
- … +4

### Valori condivisi

- const 'utf-8' → 13 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._notify_stop`
- const ',' → 11 sink: `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- const ':' → 11 sink: `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- const 1 → 10 sink: `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const b'\n' → 8 sink: `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- in http.server.path → 7 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const 404 → 6 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_POST`
- in http.server.rfile.read → 6 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- const 'Peer service error' → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_POST`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`
- const 'session_id' → 5 sink: `wg_client.py:systemd_notify`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- ext socket.AF_UNIX → 5 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- ext socket.SOCK_STREAM → 5 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- const 'Bad Request' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_POST`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'Content-Length' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_POST`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- const 'application/json' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 400 → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_POST`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- in http.server.headers → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_POST`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- ext sys.stdin → 4 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- const 'close' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 'counter' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 'invalid Content-Length' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_POST`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'mac' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 'username' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._account_request`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const 405 → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_CONNECT`, `wg_client_API_handler.py:WGClientAPIHandler.do_PATCH`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- … +18

