# `config/wg-auth.conf`

## Metadata

- Path: `config/wg-auth.conf`
- Language: `unknown`
- Lines: 19
- SHA256: `1949b56cae41e36907805e26571dba9917ba05f4ee7558617809fb14b806a5a7`

## Source

```
[auth]
fake_id = admin
login_dir = /home/main/Desktop/wg_manager/login
peer_registry = /home/main/Desktop/wg_manager/login/.peer_registry.json
ip_registry = /home/main/Desktop/wg_manager/login/.ip_registry.json

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
