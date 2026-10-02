# Snapshot del protocollo (passo 2)

- Sink analizzati: 38
- Nodi: attr=26, const=120, ext=16, in=5, open=19, param=85, shape=59, sink=38, var=119, xf=50 · archi: 922

## Canali (sink con lo stesso ricevente)

- **C1** `<senza ricevente>`
  - `wg_client.py:main` (socket.<create socket.socket>)
  - `wg_manager.py:systemd_socket` (socket.<create socket.socket>)
- **C2** `wg_auth_IPC.py:WGAuthIPC.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_auth_IPC.py:WGAuthIPC.activate` (socket.<create socket.socket>, socket.connect)
  - `wg_auth_IPC.py:WGAuthIPC.close` (socket.close, socket.shutdown)
  - `wg_auth_IPC.py:WGAuthIPC.receive_packet` (socket.recv)
  - `wg_auth_IPC.py:WGAuthIPC.send_packet` (socket.sendall)
- **C3** `wg_client_IPC.py:WGClientIPC.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._notify_stop` (socket.sendall)
  - `wg_client_IPC.py:WGClientIPC.receive_packet` (socket.recv)
  - `wg_client_IPC.py:WGClientIPC.reconcile_state` (socket.sendall)
  - `wg_client_IPC.py:WGClientIPC.send_result` (socket.sendall)
- **C4** `wg_client_activator.py:WGClientActivation.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_client_activator.py:WGClientActivation.close` (socket.close)
- **C5** `handler:wg_auth/wg_auth_API_handler.py:WGAuthAPIHandler`
  - `wg_auth_API_handler.py:WGAuthAPIHandler._read_json` (http.server.headers, http.server.rfile.read)
  - `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` (http.server.end_headers, http.server.send_header, http.server.send_response, http.server.wfile.write)
  - `wg_auth_API_handler.py:WGAuthAPIHandler.do_DELETE` (http.server.path)
  - `wg_auth_API_handler.py:WGAuthAPIHandler.do_GET` (http.server.path)
  - `wg_auth_API_handler.py:WGAuthAPIHandler.do_POST` (http.server.path)
- **C6** `handler:wg_client/wg_client_API_handler.py:WGClientAPIHandler`
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
- **C7** `wg_manager.py:reply(s)` — .wrap_socket(), 3, True, socket.socket(), ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext(), ssl.TLSVersion.TLSv1_3
  - `wg_manager.py:reply` (socket.sendall)
- **C8** `wg_manager.py:request(s)` — .wrap_socket(), 3, True, socket.socket(), ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext(), ssl.TLSVersion.TLSv1_3
  - `wg_manager.py:request` (socket.recv)
- **C9** `wg_auth_API.py:WGAuthAPI._create_server.context` — ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext()
  - `wg_auth_API.py:WGAuthAPI._create_server` (http.server.<create http.server.ThreadingHTTPServer>, socket.wrap_socket)
- **C10** `wg_client.py:systemd_notify.sock` — socket.AF_UNIX, socket.SOCK_DGRAM, socket.socket()
  - `wg_client.py:systemd_notify` (socket.<create socket.socket>, socket.close, socket.connect, socket.sendall)
- **C11** `wg_client_IPC.py:WGClientIPC._ownership_request.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._ownership_request` (socket.sendall)
- **C12** `wg_client_IPC.py:WGClientIPC._peer_request.sock` — os.dup(), socket.AF_UNIX, socket.SOCK_STREAM, socket.socket(), sys.stdin, sys.stdin.fileno()
  - `wg_client_IPC.py:WGClientIPC._peer_request` (socket.sendall)
- **C13** `wg_client_activator.py:activate_client.sock` — socket.AF_UNIX, socket.SOCK_STREAM, socket.socket()
  - `wg_client_activator.py:activate_client` (socket.<create socket.socket>, socket.close, socket.connect, socket.makefile, socket.sendall)
- **C14** `wg_controller_client.py:WGClientClient._request.conn + wg_controller_client.py:WGClientClient._request.response` — 10, http.client, http.client.HTTPSConnection(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGClientClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getheader, http.client.getresponse, http.client.read, http.client.request)
- **C15** `wg_controller_client.py:WGControllerClient._request.conn + wg_controller_client.py:WGControllerClient._request.response` — 'ca', 'controller', 'host', 'port', 'timeout', 10, http.client, http.client.HTTPSConnection(), src.wg_client.wg_client_config.load_config(), ssl.Purpose.SERVER_AUTH, ssl.create_default_context()
  - `wg_controller_client.py:WGControllerClient._request` (http.client.<create http.client.HTTPSConnection>, http.client.close, http.client.getresponse, http.client.read, http.client.request)
- **C16** `wg_manager.py:tls.ctx` — ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext(), ssl.TLSVersion.TLSv1_3
  - `wg_manager.py:tls` (socket.wrap_socket)

## Forme dei messaggi (dict che arrivano ai sink)

- `{allowed_ip: ‹in http.server.rfile.read›('allowed_ip'|'utf-8'), public_key: ‹in http.server.path›('/v1/peers/'|'auth'|'login_dir')}` — `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:202, wg_controller_client.py:85
- `{error: ?, ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_manager.py:reply` — wg_auth_API_handler.py:102, wg_auth_API_handler.py:151, wg_auth_API_handler.py:171
- `{}` — `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:277
- `{**: ‹wg_auth_API_handler.py:WGAuthAPIHandler.do_GET.status›, ok: True}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:232
- `{**: ‹wg_client_IPC.py:WGClientIPC._ownership_request(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_client_IPC.py:WGClientIPC._ownership_request.request_id›∈{1}…` — `wg_client_IPC.py:WGClientIPC._ownership_request` — wg_client_IPC.py:369
- `{**: ‹wg_client_IPC.py:WGClientIPC.send_result(fields)›, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, status: ‹wg_client_IPC.py:WGClientIPC.send_result(status)›∈{'ERROR'|'OK'}, type: 'A…` — `wg_client_IPC.py:WGClientIPC.send_result` — wg_client_IPC.py:486
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹in http.server.path›(','|'/.peer_registry.json'|'/v1/peers/'), <AUTH_MAC_HEADER>: 'mac' | ‹in http.server.path›(','|'/.peer_registry.json'|'/v1/peers/'), <AUTH_NO…` — `wg_controller_client.py:WGClientClient._request` — wg_controller_client.py:129
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(code)›∈{400|401|404|405} | ‹wg_client_API_hand…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:285
- `{<AUTH_COUNTER_HEADER>: 'counter' | ‹wg_client_API_handler.py:WGClientAPIHandler.request_auth› | ‹wg_client_API_handler.py:WGClientAPIHandler.send_json(code)›∈{200} | ‹in http.server.path,http.server…` — `wg_client_API_handler.py:WGClientAPIHandler.send_json` — wg_client_API_handler.py:285
- `{<k.lower().strip()>: ‹in socket.recv›(':'|'\r\n'|'iso-8859-1')}` — `wg_manager.py:request` — wg_manager.py:58
- `{Accept: 'application/json', Connection: 'close', Content-Length: ‹wg_controller_client.py:WGControllerClient._request.data›∈{','|':'}, Content-Type: 'application/json'}` — `wg_controller_client.py:WGControllerClient._request` — wg_controller_client.py:36
- `{activation: ‹in http.server.rfile.read›('auth'), authenticated: True, k_session: ‹wg_auth_API_handler.py:WGAuthAPIHandler.api›, ok: True, session_id: ‹wg_auth_API_handler.py:WGAuthAPIHandler.api›}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:130
- `{allowed_ip: 'allowed_ip' | ‹in socket.recv›('0'|'\r\n'|'content-length'), ok: True, operation: 'add_peer', public_key: 'public_key' | ‹in socket.recv›('0'|'\r\n'|'content-length')}` — `wg_manager.py:reply` — wg_manager.py:139
- `{allowed_ip: ‹in http.server.rfile.read›('allowed_ip'|'utf-8'), protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, public_key: ‹in http.server.path›('/.peer_registry.json'|'/v1/peers/'|'auth'…` — `wg_client_IPC.py:WGClientIPC._peer_request` — wg_client_IPC.py:288
- `{client_id: ‹wg_auth_IPC.py:WGAuthIPC.client_id›∈{'client'|'client_id'}, created_at: ?, k_session: ‹in http.server.rfile.read›('auth'|'login_dir'|'username'), listen_path: ‹wg_auth_IPC.py:WGAuthIPC.l…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:349
- `{client_id: ‹wg_client_activator.py:activate_client(client_id)›, created_at: ?, k_session: ‹wg_client_activator.py:activate_client(k_sess)›, listen_path: ‹wg_client_activator.py:activate_client(liste…` — `wg_client_activator.py:activate_client` — wg_client_activator.py:30
- `{error: 'admin principal required', protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:205
- `{error: 'authentication failed', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:142, wg_auth_API_handler.py:72
- `{error: 'internal error', ok: False}` — `wg_manager.py:reply` — wg_manager.py:217
- `{error: 'internal server error', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:113, wg_auth_API_handler.py:182
- `{error: 'invalid authentication request', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:160, wg_auth_API_handler.py:91
- `{error: 'not found', ok: False}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:199, wg_auth_API_handler.py:206, wg_auth_API_handler.py:224
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n'}, status: 'ERROR', stat…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:240
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n'}, status: 'ERROR', stat…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:251
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n'}, status: 'ERROR', stat…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:263
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n'}, status: 'ERROR', status_co…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:153
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n'}, status: 'ERROR', status_co…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:165
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_peer_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n'}, status: 'ERROR', status_co…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:177
- `{error: ?, protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, status: 'ERROR', type: 'STATE_RESULT'}` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:379
- `{error: ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(message)›∈{'Bad Request'|'Peer service error'|'Unauthorized'}, message: ‹wg_client_API_handler.py:WGClientAPIHandler.send_error(explain…` — `wg_client_API_handler.py:WGClientAPIHandler.send_error` — wg_client_API_handler.py:322
- `{interface: 'if' | ‹wg_manager.py:main.c›, ok: True, peers: 'if' | ‹wg_manager.py:main.c›}` — `wg_manager.py:reply` — wg_manager.py:152
- `{ok: True, operation: 'remove_peer', public_key: '/v1/peers/' | ‹in socket.recv›('0'|'\r\n'|'content-length')}` — `wg_manager.py:reply` — wg_manager.py:147
- `{ok: True, response: ‹in http.server.rfile.read›('pub'|'username')}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:62
- `{ok: True}` — `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — wg_auth_API_handler.py:217
- `{peers: ‹wg_client_IPC.py:WGClientIPC.reconcile_state(peers)›∈{'k_session'|'listen_path'|'principal'|'session_id'}, protocol_version: ‹wg_client_IPC.py:PROTOCOL_VERSION›∈{1}, type: 'STATE_SNAPSHOT'}` — `wg_client_IPC.py:WGClientIPC.reconcile_state` — wg_client_IPC.py:441
- `{protocol_version: ‹wg_auth_IPC.py:PROTOCOL_VERSION›∈{1}, request_id: ‹wg_auth_IPC.py:WGAuthIPC._handle_ownership_request.request_id›∈{'request_id'|'utf-8'|0|1|b'\n'}, result: ‹wg_auth_IPC.py:WGAuthI…` — `wg_auth_IPC.py:WGAuthIPC.send_packet` — wg_auth_IPC.py:273
- … +5

## Cosa accettano i parametri (valori costanti che possono assumere)

- `wg_controller_client.py:WGControllerClient._request(path)` ∈ {'/.peer_registry.json' | '/v1/peers' | '/v1/peers/' | '/v1/status' | 'auth' | 'login_dir' | 'peer_registry' | 'username'}
- `wg_client.py:systemd_notify(message)` ∈ {'READY=1' | 'STATUS=session_id=' | 'STOPPING=1' | 'k_session' | 'listen_path' | 'principal' | 'session_id'}
- `wg_controller_client.py:WGClientClient._request(path)` ∈ {'/.peer_registry.json' | '/v1/peers/' | '/v1/status' | 'auth' | 'login_dir' | 'peer_registry' | 'username'}
- `wg_auth_API_handler.py:WGAuthAPIHandler._send_json(status)` ∈ {200 | 400 | 401 | 404 | 409 | 500}
- `wg_client_API_handler.py:WGClientAPIHandler.send_json(obj)` ∈ {'/owner' | '/v1/admin/peers/' | '/v1/peers/' | 'allowed_ip' | 'username' | 'utf-8'}
- `wg_client_IPC.py:WGClientIPC._peer_request(public_key)` ∈ {'/.peer_registry.json' | '/v1/peers/' | 'auth' | 'login_dir' | 'peer_registry' | 'username'}
- `wg_client_IPC.py:WGClientIPC.unregister_peer(public_key)` ∈ {'/.peer_registry.json' | '/v1/peers/' | 'auth' | 'login_dir' | 'peer_registry' | 'username'}
- `wg_controller_client.py:WGClientClient.remove_peer(public_key)` ∈ {'/.peer_registry.json' | '/v1/peers/' | 'auth' | 'login_dir' | 'peer_registry' | 'username'}
- `wg_controller_client.py:WGControllerClient.remove_peer(public_key)` ∈ {'/.peer_registry.json' | '/v1/peers/' | 'auth' | 'login_dir' | 'peer_registry' | 'username'}
- `wg_peer_service.py:WGPeerService.remove_peer(public_key)` ∈ {'/.peer_registry.json' | '/v1/peers/' | 'auth' | 'login_dir' | 'peer_registry' | 'username'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(explain)` ∈ {'Invalid ownership request' | 'Invalid peer request' | 'invalid Content-Length' | 'invalid secure-session authentication' | 'secure-session authentication failed'}
- `wg_auth_IPC.py:WGAuthIPC.__init__(principal)` ∈ {'auth' | 'login_dir' | 'username' | b'wg-manager'}
- `wg_auth_IPC.py:WGAuthIPC._handle_ownership_request(request)` ∈ {'utf-8' | 0 | 1 | b'\n'}
- `wg_auth_IPC.py:WGAuthIPC._handle_peer_request(request)` ∈ {'utf-8' | 0 | 1 | b'\n'}
- `wg_auth_IPC.py:WGAuthIPC.activate(k_session)` ∈ {'auth' | 'login_dir' | 'username' | b'wg-manager'}
- `wg_auth_IPC.py:WGAuthIPC.activate(session_id)` ∈ {'auth' | 'login_dir' | 'username' | b'wg-manager'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(code)` ∈ {400 | 401 | 404 | 405}
- `wg_client_IPC.py:WGClientIPC.reconcile_state(peers)` ∈ {'k_session' | 'listen_path' | 'principal' | 'session_id'}
- `wg_client_API_handler.py:WGClientAPIHandler.send_error(message)` ∈ {'Bad Request' | 'Peer service error' | 'Unauthorized'}
- `wg_client_IPC.py:WGClientIPC.register_peer(public_key)` ∈ {'/v1/peers/' | 'auth' | 'login_dir'}
- `wg_controller_client.py:WGClientClient._request(method)` ∈ {'DELETE' | 'GET' | 'PUT'}
- `wg_controller_client.py:WGClientClient.add_peer(public_key)` ∈ {'/v1/peers/' | 'auth' | 'login_dir'}
- `wg_controller_client.py:WGControllerClient.__init__(timeout)` ∈ {'controller' | 'timeout' | 10}
- `wg_controller_client.py:WGControllerClient._request(method)` ∈ {'DELETE' | 'GET' | 'POST'}
- … +24

## Sink

### `wg_auth_API.py:WGAuthAPI._create_server` — http.server.<create http.server.ThreadingHTTPServer>@L373, socket.wrap_socket@L399
- via: .wrap_socket, configparser.ConfigParser, http.server.ThreadingHTTPServer, ssl.SSLContext
- costanti dirette: 'host', 'http', 'port'
- esterni: ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER

### `wg_auth_API_handler.py:WGAuthAPIHandler._read_json` — http.server.headers@L28, http.server.rfile.read@L31
- costanti dirette: '0', 'Content-Length'
- dalla rete: http.server.headers

### `wg_auth_API_handler.py:WGAuthAPIHandler._send_json` — http.server.end_headers@L23, http.server.send_header@L21, http.server.send_header@L22, http.server.send_response@L20, http.server.wfile.write@L25
- via: json.dumps
- costanti dirette: ',', ':', 'Content-Length', 'Content-Type', 'application/json', 'utf-8', 200, 400, 401, 404, 409, 500
- forme: 17 (vedi sopra)

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_DELETE` — http.server.path@L203

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_GET` — http.server.path@L221

### `wg_auth_API_handler.py:WGAuthAPIHandler.do_POST` — http.server.path@L189, http.server.path@L193

### `wg_auth_IPC.py:WGAuthIPC.activate` — socket.<create socket.socket>@L342, socket.connect@L347
- via: configparser.ConfigParser
- costanti dirette: 'client', 'socket_path'
- esterni: socket.AF_UNIX, socket.SOCK_STREAM

### `wg_auth_IPC.py:WGAuthIPC.close` — socket.close@L440, socket.shutdown@L435
- esterni: socket.SHUT_RDWR

### `wg_auth_IPC.py:WGAuthIPC.receive_packet` — socket.recv@L285
- costanti dirette: 4096

### `wg_auth_IPC.py:WGAuthIPC.send_packet` — socket.sendall@L428
- via: json.dumps
- costanti dirette: ',', ':', 'utf-8', b'\n'
- forme: 13 (vedi sopra)

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
- via: .peer_owners, .release, configparser.ConfigParser, json.dumps, src.wg_auth.wg_auth_peer_registry.WGAuthPeerRegistry, src.wg_auth.wg_auth_user_store.WGAuthUserStore, ssl.create_default_context, urllib.parse.quote, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: ',', '/.peer_registry.json', '/v1/peers/', '/v1/status', ':', 'DELETE', 'GET', 'PUT', 'auth', 'login_dir', 'peer_registry', 'username' (+1)
- esterni: src.wg_client.wg_client_API_handler.AUTH_COUNTER_HEADER, src.wg_client.wg_client_API_handler.AUTH_MAC_HEADER, src.wg_client.wg_client_API_handler.AUTH_SESSION_ID_HEADER, ssl.Purpose.SERVER_AUTH
- dalla rete: http.server.path
- input aperti alle radici: input wg_auth_API.py:WGAuthAPI._reassign_ownership(public_key), input wg_auth_API.py:WGAuthAPI._reassign_ownership(username), input wg_auth_API.py:WGAuthAPI._register_peer(username), input wg_auth_API.py:WGAuthAPI._unregister_peer(public_key), input wg_auth_API.py:WGAuthAPI._unregister_peer(username), input wg_controller_client.py:WGClientClient.__init__(ca), input wg_controller_client.py:WGClientClient.__init__(host), input wg_controller_client.py:WGClientClient.__init__(listen_path), input wg_controller_client.py:WGClientClient.__init__(port), input wg_controller_client.py:WGClientClient.__init__(timeout)
- forme: 2 (vedi sopra)

### `wg_controller_client.py:WGControllerClient._request` — http.client.<create http.client.HTTPSConnection>@L32, http.client.close@L74, http.client.getresponse@L49, http.client.read@L50, http.client.request@L47
- via: .peer_owners, .release, configparser.ConfigParser, json.dumps, src.wg_auth.wg_auth_peer_registry.WGAuthPeerRegistry, src.wg_auth.wg_auth_user_store.WGAuthUserStore, src.wg_client.wg_client_config.load_config, ssl.create_default_context, urllib.parse.quote, urllib.parse.unquote, urllib.parse.urlsplit
- costanti dirette: ',', '/.peer_registry.json', '/v1/peers', '/v1/peers/', '/v1/status', ':', 'DELETE', 'GET', 'POST', 'auth', 'ca', 'controller' (+7)
- esterni: ssl.Purpose.SERVER_AUTH
- dalla rete: http.server.path
- input aperti alle radici: input wg_auth_API.py:WGAuthAPI._reassign_ownership(public_key), input wg_auth_API.py:WGAuthAPI._reassign_ownership(username), input wg_auth_API.py:WGAuthAPI._unregister_peer(public_key), input wg_auth_API.py:WGAuthAPI._unregister_peer(username)
- forme: 2 (vedi sopra)

### `wg_manager.py:reply` — socket.sendall@L40
- via: http.HTTPStatus, json.dumps
- costanti dirette: ' ', ',', ':', 'HTTP/1.1 ', '\r\nCache-Control: no-store\r\nConnection: clo…, '\r\nContent-Type: application/json\r\nContent-…, 200, 201, 500
- forme: 5 (vedi sopra)

### `wg_manager.py:request` — socket.recv@L47, socket.recv@L71
- costanti dirette: '0', 'content-length', 1, 4096, b'\r\n\r\n'
- dalla rete: socket.recv
- forme: 1 (vedi sopra)

### `wg_manager.py:systemd_socket` — socket.<create socket.socket>@L175
- costanti dirette: 3

### `wg_manager.py:tls` — socket.wrap_socket@L188
- via: socket.socket
- costanti dirette: 3

## Intersezioni (nodi condivisi da piu' sink)

- param `wg_auth_API.py:WGAuthAPI.__init__(config)` → 6 sink: `wg_auth_API.py:WGAuthAPI._create_server`, `wg_auth_IPC.py:WGAuthIPC.activate`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_IPC.py:WGClientIPC._peer_request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.obj` → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.path` → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- var `wg_client_IPC.py:PROTOCOL_VERSION` → 5 sink: `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- attr `wg_auth_API.py:WGAuthAPI.user_store` → 4 sink: `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE.public_key` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.allowed_ip` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- var `wg_client_API_handler.py:WGClientAPIHandler.do_PUT.public_key` → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- attr `wg_auth_API.py:WGAuthAPI.config` → 3 sink: `wg_auth_API.py:WGAuthAPI._create_server`, `wg_auth_IPC.py:WGAuthIPC.activate`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- var `wg_auth_API_handler.py:WGAuthAPIHandler._handle_auth_start.username` → 2 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`
- var `wg_client.py:activate.activation` → 2 sink: `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- var `wg_client.py:activate.cfg` → 2 sink: `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_controller_client.py:WGControllerClient._request`
- … +4

### Valori condivisi

- const ':' → 12 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const 'utf-8' → 12 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- const ',' → 11 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const 1 → 10 sink: `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const 'username' → 7 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const 404 → 7 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`
- in http.server.rfile.read → 7 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`
- const b'\n' → 6 sink: `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_IPC.py:WGClientIPC._notify_stop`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- in http.server.path → 6 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._ownership_request`, `wg_client_IPC.py:WGClientIPC._peer_request`
- ext socket.AF_UNIX → 6 sink: `wg_auth_IPC.py:WGAuthIPC.activate`, `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- ext socket.SOCK_STREAM → 6 sink: `wg_auth_IPC.py:WGAuthIPC.activate`, `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- const '/v1/peers/' → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 'Content-Length' → 5 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._read_json`, `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'allowed_ip' → 5 sink: `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`, `wg_controller_client.py:WGControllerClient._request`
- const 'application/json' → 5 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_controller_client.py:WGClientClient._request`
- const 'auth' → 5 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_auth_IPC.py:WGAuthIPC.send_packet`, `wg_client_IPC.py:WGClientIPC._peer_request`, `wg_controller_client.py:WGClientClient._request`
- const 'session_id' → 5 sink: `wg_client.py:systemd_notify`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`, `wg_client_IPC.py:WGClientIPC.reconcile_state`
- const 'Peer service error' → 4 sink: `wg_client_API_handler.py:WGClientAPIHandler.do_DELETE`, `wg_client_API_handler.py:WGClientAPIHandler.do_GET`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 400 → 4 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- in http.server.headers → 4 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._read_json`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- ext sys.stdin → 4 sink: `wg_client.py:main`, `wg_client.py:systemd_notify`, `wg_client_IPC.py:WGClientIPC.reconcile_state`, `wg_client_IPC.py:WGClientIPC.send_result`
- const '0' → 3 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._read_json`, `wg_manager.py:reply`, `wg_manager.py:request`
- const 'Bad Request' → 3 sink: `wg_client_API_handler.py:WGClientAPIHandler.authenticate_request`, `wg_client_API_handler.py:WGClientAPIHandler.do_PUT`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`
- const 'Content-Type' → 3 sink: `wg_auth_API_handler.py:WGAuthAPIHandler._send_json`, `wg_client_API_handler.py:WGClientAPIHandler.send_error`, `wg_client_API_handler.py:WGClientAPIHandler.send_json`
- … +38

