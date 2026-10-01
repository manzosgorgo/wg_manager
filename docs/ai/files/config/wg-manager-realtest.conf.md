# `config/wg-manager-realtest.conf`

## Metadata

- Path: `config/wg-manager-realtest.conf`
- Language: `unknown`
- Lines: 10
- SHA256: `61a583477db7b59d1c28083111ca8bd88e91dd69a3815771475b52a75211f397`

## Source

```
[manager]
interface = wg0

[tls]
server_cert =/home/main/Desktop/wg_manager/cert/server.crt
server_key = /home/main/Desktop/wg_manager/cert/server.key
client_ca = /home/main/Desktop/wg_manager/cert/ca.crt

[policy]
vpn_network = 10.8.0.0/24
```
