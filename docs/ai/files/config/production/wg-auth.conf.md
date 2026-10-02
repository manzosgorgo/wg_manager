# `config/production/wg-auth.conf`

## Metadata

- Path: `config/production/wg-auth.conf`
- Language: `unknown`
- Lines: 20
- SHA256: `10e5eedbbce5da9a27face8bd89b633da6cbf4f156fe397a609d479bfd51c40e`

## Source

```
[auth]
fake_id = admin
login_dir = /var/lib/wg-manager/auth
peer_registry = /var/lib/wg-manager/auth/.peer_registry.json
ip_registry = /var/lib/wg-manager/auth/.ip_registry.json

[client]
socket_path = /run/wg-manager/wg-client.sock
client_id = wg-auth
timeout = 3600
idle_timeout = 45
listen_path = /postauth

[http]
host = 127.0.0.1
port = 9445
server_cert = /etc/wg-manager/cert/auth/auth.crt
server_key = /etc/wg-manager/cert/auth/auth.key
ca_cert = /etc/wg-manager/cert/ca.crt
require_client_cert = false
```
