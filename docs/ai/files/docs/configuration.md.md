# `docs/configuration.md`

## Metadata

- Path: `docs/configuration.md`
- Language: `markdown`
- Lines: 196
- SHA256: `b4de2e1bda7aa836e392dade14a8666f6c0cc4532dda8167f86e7d451b95fe59`

## Source

```markdown
# Reference della configurazione production

I file production installati dai package sono:

```text
/etc/wg-manager/wg-auth.conf
/etc/wg-manager/wg-client.conf
/etc/wg-manager/wg-manager.conf
/etc/apache2/conf-available/wg-manager.conf
```

I valori nella repository sotto `config/production/` sono i template
installati dai package.

## wg-auth.conf

### [auth]

`fake_id`
: Identità usata dal flusso OPAQUE quando serve una risposta indistinguibile
  per utenti inesistenti. Il valore production corrente è `admin`.

`login_dir`
: Directory persistente dei record utente OPAQUE.
  Production: `/var/lib/wg-manager/auth`.

`peer_registry`
: Registry persistente `public_key -> owner/IP`.

`ip_registry`
: Registry persistente `allowed_ip -> public_key/owner`.

### [client]

`socket_path`
: Socket Unix usato da `wg-auth` per attivare `wg-client`.
  Deve corrispondere a `wg-client.socket`.

`client_id`
: Identificatore usato durante l'activation.

`timeout`
: Durata massima della sessione attivata, in secondi.

`idle_timeout`
: Timeout di inattività applicativo, in secondi.

`listen_path`
: Prefix HTTP esposto dal client per-sessione. Production: `/postauth`.

### [http]

`host`, `port`
: Bind locale dell'API auth. Production usa `127.0.0.1:9445`, raggiunta da
  Apache.

`server_cert`, `server_key`
: Certificato e private key TLS di `wg-auth`.

`ca_cert`
: CA usata dal servizio.

`require_client_cert`
: Se `true`, richiede certificato client sull'API auth. Il deployment
  production corrente usa `false`, perché il browser passa da Apache.

## wg-client.conf

### [client]

`name`
: Nome logico del client.

`log_level`
: Livello di logging applicativo.

### [api]

`host`, `port`
: Bind dell'API per-sessione. Production usa `127.0.0.1:9444`.

`server_cert`, `server_key`
: Certificato TLS del client API.

`ca`
: CA di trust.

### [controller]

`host`
: **Da configurare.** IP o DNS dell'host che esegue
  `wg-manager-controller`.

`port`
: Porta HTTPS del controller. Production: `9443`.

`ca`
: CA usata per verificare il controller.

`client_cert`, `client_key`
: Credenziale mTLS con cui `wg-client` si autentica al controller.

`timeout`
: Timeout delle richieste verso il controller.

### [wireguard]

`interface`
: Nome dell'interfaccia WireGuard amministrata. Production: `wg0`.

`endpoint`
: **Da configurare.** Endpoint pubblico inserito nelle configurazioni client,
  ad esempio `vpn.example.net:51820`. Il valore
  `vpn.example.invalid:51820` è intenzionalmente un placeholder.

### [secure_session]

`enabled`
: Abilita la secure session applicativa.

`session_id_size`
: Dimensione in byte del session ID.

`nonce_size`
: Dimensione del nonce.

`session_key_size`
: Dimensione delle chiavi derivate locali. Non è la dimensione della
  `K_session` OPAQUE.

`counter_min`, `counter_max`
: Range valido del counter anti-replay.

Il codice supporta inoltre default per `session_timeout`,
`max_request_frequency` e `replay_window_size` anche quando non sono
specificati nel file.

## wg-manager.conf

### [manager]

`interface`
: Interfaccia WireGuard sulla macchina controller.

### [tls]

`server_cert`, `server_key`
: Certificato e private key TLS del controller.

`client_ca`
: CA usata per validare il certificato mTLS presentato da `wg-client`.

### [policy]

`vpn_network`
: Rete dalla quale possono essere assegnati gli IP dei peer.

`server_address`
: Indirizzo del server WireGuard riportato nei dati di provisioning.

## Apache

La configurazione installata in
`/etc/apache2/conf-available/wg-manager.conf` espone:

```text
/vpn/       frontend statico
/js/        moduli JavaScript
/vendor/    libreria QR
/auth       proxy verso wg-auth
/status     proxy verso wg-auth
/postauth/  proxy verso wg-client
```

Apache usa:

```text
/etc/wg-manager/cert/ca.crt
/etc/wg-manager/cert/apache/apache-client.pem
```

per verificare i backend e autenticarsi a `wg-client`.

La configurazione non viene abilitata automaticamente dal package.

## Placeholder da eliminare prima del deployment

Il template production di `wg-client.conf` contiene intenzionalmente:

```ini
host = wg-manager-controller
endpoint = vpn.example.invalid:51820
```

Il checker `wg-manager-check-auth-client` segnala questi valori finché non
vengono sostituiti.
```
