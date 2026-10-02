# `config/production/wg-manager.conf`

## Metadata

- Path: `config/production/wg-manager.conf`
- Language: `unknown`
- Lines: 12
- SHA256: `a7fc4d87f110d9d3d30ac193ddb7c6eb52f3d292b1e592889180f2649fb54e98`

## Source

```
[manager]
interface = wg0

[tls]
server_cert = /etc/wg-manager/cert/controller/server.crt
server_key = /etc/wg-manager/cert/controller/server.key
client_ca = /etc/wg-manager/cert/ca.crt

[policy]
vpn_network = 10.8.0.0/24
# Address assigned to the WireGuard server itself. Used for client provisioning.
server_address = 10.8.0.1/24
```
