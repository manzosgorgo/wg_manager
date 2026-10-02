# `config/production/wg-client.conf`

## Metadata

- Path: `config/production/wg-client.conf`
- Language: `unknown`
- Lines: 34
- SHA256: `7294355e10d11190c82581534cca3b03ed74e5554f1b41c9e4fad068ce0b8493`

## Source

```
[client]
name = wg-client
log_level = INFO

[api]
host = 127.0.0.1
port = 9444
server_cert = /etc/wg-manager/cert/client/client.crt
server_key = /etc/wg-manager/cert/client/client.key
ca = /etc/wg-manager/cert/ca.crt

[controller]
# Set this to the DNS name or address of the machine running
# wg-manager-controller.
host = wg-manager-controller
port = 9443
ca = /etc/wg-manager/cert/ca.crt
client_cert = /etc/wg-manager/cert/client/client.crt
client_key = /etc/wg-manager/cert/client/client.key
timeout = 10

[wireguard]
interface = wg0
# Public endpoint written into generated client configurations.
# Change this before provisioning peers.
endpoint = vpn.example.invalid:51820

[secure_session]
enabled = true
session_id_size = 16
nonce_size = 32
session_key_size = 32
counter_min = 1
counter_max = 4294967295
```
