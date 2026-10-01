# `config/wg-auth.conf`

## Metadata

- Path: `config/wg-auth.conf`
- Language: `unknown`
- Lines: 17
- SHA256: `4c46f20567b525f64eb96e709a51c98a0b8b8020117601905728df0b3b1c6be0`

## Source

```
[auth]
fake_id = test-user
login_dir = /home/main/Desktop/wg_manager/login

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
