# `config/wg-manager-captest.conf`

## Metadata

- Path: `config/wg-manager-captest.conf`
- Language: `unknown`
- Lines: 10
- SHA256: `adf1febd403dbb2203c6af3fbe0b3d2e5ed9409e660d17fae4322eadbacc5253`

## Source

```
[manager]
interface = wg-test

[tls]
server_cert =/home/main/Desktop/wg_manager/cert/server.crt
server_key = /home/main/Desktop/wg_manager/cert/server.key
client_ca = /home/main/Desktop/wg_manager/cert/ca.crt

[policy]
vpn_network = 10.8.0.0/24
```
