# `config/wg-client-test-auth.conf`

## Metadata

- Path: `config/wg-client-test-auth.conf`
- Language: `unknown`
- Lines: 35
- SHA256: `b13ce1abf52bb31ff80d08bf5f14e483bee759f99f2cdbcf1d806a2fbfcd7d90`

## Source

```
[client]
name = wg-client
log_level = DEBUG



[api]
host = 127.0.0.1
port = 9444
server_cert = /home/main/Desktop/wg_manager/cert/server.crt
server_key = /home/main/Desktop/wg_manager/cert/server.key
ca = /home/main/Desktop/wg_manager/cert/ca.crt


[controller]
host = 127.0.0.1
port = 9443
ca = /home/main/Desktop/wg_manager/cert/ca.crt
client_cert = /home/main/Desktop/wg_manager/cert/client.crt
client_key = /home/main/Desktop/wg_manager/cert/client.key
timeout = 10


[wireguard]
interface = wg0
endpoint = 127.0.0.1:51820

[secure_session]
enabled = true

session_id_size = 16
nonce_size = 32
session_key_size = 32
counter_min = 1
counter_max = 4294967295
```
