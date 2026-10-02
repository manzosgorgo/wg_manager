# Snapshot del protocollo (passo 2)

- Sink analizzati: 4
- Nodi: const=44, ext=6, in=1, param=4, shape=9, sink=4, var=21, xf=14 · archi: 160

## Canali (sink con lo stesso ricevente)

- **C1** `<senza ricevente>`
  - `wg_manager.py:systemd_socket` (socket.<create socket.socket>)
- **C2** `wg_manager.py:reply(s)` — .wrap_socket(), 3, True, socket.socket(), ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext(), ssl.TLSVersion.TLSv1_3
  - `wg_manager.py:reply` (socket.sendall)
- **C3** `wg_manager.py:request(s)` — .wrap_socket(), 3, True, socket.socket(), ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext(), ssl.TLSVersion.TLSv1_3
  - `wg_manager.py:request` (socket.recv)
- **C4** `wg_manager.py:tls.ctx` — ssl.CERT_REQUIRED, ssl.PROTOCOL_TLS_SERVER, ssl.SSLContext(), ssl.TLSVersion.TLSv1_3
  - `wg_manager.py:tls` (socket.wrap_socket)

## Forme dei messaggi (dict che arrivano ai sink)

- `{<k.lower().strip()>: ‹in socket.recv›(':'|'\r\n'|'iso-8859-1')}` — `wg_manager.py:request` — wg_manager.py:59
- `{allowed_ip: 'allowed_ip' | ‹in socket.recv›('0'|'\r\n'|'content-length'), ok: True, operation: 'add_peer', public_key: 'public_key' | ‹in socket.recv›('0'|'\r\n'|'content-length')}` — `wg_manager.py:reply` — wg_manager.py:177
- `{error: 'internal error', ok: False}` — `wg_manager.py:reply` — wg_manager.py:257
- `{error: ?, ok: False}` — `wg_manager.py:reply` — wg_manager.py:246
- `{interface: 'if' | ‹wg_manager.py:main.c›, listen_port: '\t' | 'dump' | 'if' | 'show' | 0 | +7, ok: True, server_address: 'server_address' | ‹wg_manager.py:main.c›, server_public_key: '\t' | 'dump' |…` — `wg_manager.py:reply` — wg_manager.py:149
- `{interface: 'if' | ‹wg_manager.py:main.c›, ok: True, peers: 'if' | ‹wg_manager.py:main.c›}` — `wg_manager.py:reply` — wg_manager.py:190
- `{ok: True, operation: 'remove_peer', public_key: '/v1/peers/' | ‹in socket.recv›('0'|'\r\n'|'content-length')}` — `wg_manager.py:reply` — wg_manager.py:185

## Cosa accettano i parametri (valori costanti che possono assumere)

- `wg_manager.py:reply(code)` ∈ {200 | 201 | 500}
- `wg_manager.py:reply(obj)` ∈ {200 | 201}

## Sink

### `wg_manager.py:reply` — socket.sendall@L41
- via: http.HTTPStatus, json.dumps
- costanti dirette: ' ', ',', ':', 'HTTP/1.1 ', '\r\nCache-Control: no-store\r\nConnection: clo…, '\r\nContent-Type: application/json\r\nContent-…, 200, 201, 500
- forme: 6 (vedi sopra)

### `wg_manager.py:request` — socket.recv@L48, socket.recv@L72
- costanti dirette: '0', 'content-length', 1, 4096, b'\r\n\r\n'
- dalla rete: socket.recv
- forme: 1 (vedi sopra)

### `wg_manager.py:systemd_socket` — socket.<create socket.socket>@L215
- costanti dirette: 3

### `wg_manager.py:tls` — socket.wrap_socket@L228
- via: socket.socket
- costanti dirette: 3

## Intersezioni (nodi condivisi da piu' sink)

_nessun nodo con nome condiviso_

### Valori condivisi

- const '0' → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`
- const ':' → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`
- const '\r\n' → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`
- const 'content-length' → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`
- const 'iso-8859-1' → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`
- const 1 → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`
- const 3 → 2 sink: `wg_manager.py:systemd_socket`, `wg_manager.py:tls`
- const b'\r\n\r\n' → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`
- in socket.recv → 2 sink: `wg_manager.py:reply`, `wg_manager.py:request`

