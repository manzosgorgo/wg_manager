# `config/wg-auth.conf`

## Metadata

- Path: `config/wg-auth.conf`
- Language: `unknown`
- Lines: 18
- SHA256: `818c6e45460ae1d2d27ca4f5f1d8d7e7fd56a2d18c2940b34b57796d665cdd54`

## Source

```
[auth]
fake_id = admin
login_dir = /home/main/Desktop/wg_manager/login
peer_registry = /home/main/Desktop/wg_manager/login/.peer_registry.json

[client]
socket_path = /run/wg_manager/wg-client-test.sock
client_id = wg-auth
timeout = 10
listen_path = /postauth

[http]
host = 127.0.0.1
port = 9445
server_cert = /home/main/Desktop/wg_manager/cert/auth.crt
server_key = /home/main/Desktop/wg_manager/cert/auth.key
ca_cert = /home/main/Desktop/wg_manager/cert/ca.crt
require_client_cert = false
```
