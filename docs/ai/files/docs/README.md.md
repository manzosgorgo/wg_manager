# `docs/README.md`

## Metadata

- Path: `docs/README.md`
- Language: `markdown`
- Lines: 405
- SHA256: `5a853b0a037799ec7815e4555c3b99e7ab8f47fff3d2898f0d42c604836e273d`

## Source

```markdown
# wg-manager documentation

Automatically generated documentation for the `wg_manager` project.

> This repository contains generated documentation and analysis artifacts.
> It is observational documentation of the current project tree, not a
> normative architecture specification.

## Project analysis

- [AI index](ai/README.md)
- [Project tree](ai/TREE.md)
- [Modules](ai/MODULES.md)
- [Dependencies](ai/DEPENDENCIES.md)
- [Symbols](ai/SYMBOLS.md)
- [Connections](ai/CONNECTIONS.md)

## Protocol snapshots

- [wg-auth protocol](ai/wg_auth_proto.md)
- [wg-client protocol](ai/wg_client_proto.md)
- [wg-manager protocol](ai/wg_manager_proto.md)
- [wg-all protocol](ai/wg_all_proto.md)

## Python API documentation

- [pydoc API index](ai/pydoc/index.html)

The Python API reference is generated from module/class/function docstrings
with `tools/build_pydoc.py`.

## Source documentation

The [`ai/files/`](ai/files/) directory contains generated documentation
for the individual source files discovered by the project indexer.

## Generation

The documentation is generated mechanically from the `wg_manager` source
tree using the analysis tools in the project.

The protocol snapshots are generated independently for:

- `src/wg_auth`
- `src/wg_client`
- `src/wg_manager`

# Documentazione Principale di wg_manager
# wg_manager

Backend modulare per autenticare utenti, creare sessioni applicative sicure e
gestire peer WireGuard mantenendo separati autenticazione, autorizzazione e
privilegi di rete.

Questo documento descrive l'implementazione corrente del progetto.

## Architettura

```text
Browser / frontend
       |
       | OPAQUE
       v
   wg-auth :9445
       |
       | IPC Unix persistente
       | activation + reconciliation + persistence/admin RPC
       v
   wg-client :9444
       |
       | HTTPS mTLS
       v
   wg-manager :9443
       |
       | wg / mock
       v
    WireGuard
```

### wg-auth

`wg-auth` gestisce:

- autenticazione OPAQUE;
- stato della sessione autenticata;
- account persistenti;
- ownership dei peer;
- registry globale peer/IP;
- attivazione e shutdown di `wg-client`.

I record utente sono salvati in `login/<username>` e contengono il record
OPAQUE e l'elenco dei peer posseduti.

Gli indici globali sono:

```text
login/.peer_registry.json   public_key -> allowed_ip / owner / state
login/.ip_registry.json     allowed_ip -> public_key / owner / state
```

I registry sono indici derivati. Le sorgenti autorevoli restano:

- `wg-manager` / WireGuard per i peer realmente presenti;
- `login/<username>` per l'ownership persistita.

All'attivazione `wg-client` legge lo stato live dal manager e invia uno
`STATE_SNAPSHOT` a `wg-auth`, che ricostruisce entrambi i registry.

Un peer live senza owner persistito viene classificato `orphan` e può essere
riparato dall'amministratore. Ownership multiple, IP duplicati e snapshot
malformati restano errori fatal della reconciliation.

### wg-client

`wg-client` è un processo per-sessione avviato via systemd socket activation.

Responsabilità principali:

- validazione del pacchetto di activation;
- `WGSecureSession` obbligatoria;
- autenticazione HMAC di request e response;
- replay window e counter;
- autorizzazione per-owner;
- orchestrazione tra persistence e controller;
- API HTTPS per utenti e amministratore.

La secure session deriva chiavi request/response da una `K_session` OPAQUE
di 64 byte tramite HKDF-SHA256. `session_key_size` indica la dimensione delle
chiavi locali derivate (32 byte nella configurazione corrente), non la
dimensione della `K_session`.

### wg-manager

`wg-manager` è il componente privilegiato e resta volutamente piccolo.

Conosce solo policy WireGuard:

- formato chiavi;
- subnet VPN;
- duplicate public key;
- duplicate allowed IP;
- operazioni `wg show/set`.

Non conosce account, username o ownership applicativa.

Il servizio gira come `wg-manager` con `CAP_NET_ADMIN`; in sviluppo può
usare `mock/mock` tramite `WG_PROGRAM`.

## Flusso di autenticazione e activation

```text
frontend
   |
   | POST /auth
   | POST /auth/verify
   v
wg-auth
   |
   | activation packet
   v
wg-client
   |
   | GET controller /v1/status
   v
wg-manager
   |
   | live peer snapshot
   v
wg-client
   |
   | STATE_SNAPSHOT
   v
wg-auth
   |
   | rebuild peer/ip registry
   | STATE_RESULT
   v
wg-client
   |
   | bind HTTPS API
   | ACTIVATION_RESULT OK
   v
session ACTIVE
```

L'activation non viene dichiarata riuscita finché bind HTTPS e reconciliation
non sono completati.

## API

Tutte le API di `wg-client` sono sotto il `listen_path` assegnato alla
sessione e richiedono gli header di `WGSecureSession`.

### Utente

```text
GET    /v1/status
PUT    /v1/peers/<public_key>
DELETE /v1/peers/<public_key>
```

Gli utenti normali vedono e possono modificare solo i peer posseduti.

### Amministratore

```text
GET    /v1/admin/peers
PUT    /v1/admin/peers/<public_key>/owner
POST   /v1/admin/users
DELETE /v1/admin/users/<username>
```

La vista admin unisce:

- stato runtime del manager;
- ownership persistita;
- stato `consistent/orphan/stale`;
- indice IP;
- lista utenti.

Il reassignment di ownership non modifica WireGuard.

### wg-manager

Il controller locale espone:

```text
GET    /v1/status
POST   /v1/peers
DELETE /v1/peers/<public_key>
```

ed è raggiunto da `wg-client` tramite HTTPS mTLS.

## Consistency model

Creazione peer:

```text
reserve ownership + IP
        |
        v
manager add
        |
        v
session ownership update
```

Se il manager fallisce, la reservation viene rollbackata.

Rimozione peer:

```text
manager remove
      |
      v
ownership cleanup
      |
      v
session ownership update
```

Se il manager ha già rimosso il peer ma la persistence fallisce, l'API
restituisce un errore di consistenza `502`: il peer è già stato rimosso e lo
stato deve essere riparato/reconciliato.

La protezione contro crash nel mezzo di operazioni multi-processo è affidata
alla combinazione di write atomiche, rollback best-effort, reconciliation
all'attivazione e strumenti admin di repair. Un protocollo transazionale più
forte è rimandato a una fase successiva.

## IPC wg-auth <-> wg-client

Il canale Unix persistente trasporta attualmente:

```text
ACTIVATION / ACTIVATION_RESULT
STATE_SNAPSHOT / STATE_RESULT
PEER_REGISTER / PEER_UNREGISTER / PEER_RESULT
OWNERSHIP_STATE / OWNERSHIP_REASSIGN / OWNERSHIP_RESULT
ACCOUNT_CREATE / ACCOUNT_DELETE / ACCOUNT_RESULT
STOP
```

Le operazioni ownership/account sono autorizzate nuovamente lato `wg-auth`;
non ci si affida solo al controllo HTTP di `wg-client`.

## systemd

Unit principali:

```text
wg-client-test.socket
wg-client-test@.service
wg-controller-test.socket
wg-controller-test@.service
```

Il socket client è:

```ini
SocketUser=wg-client
SocketGroup=wg-client
SocketMode=0660
Accept=yes
```

Il controller gira come `wg-manager` con `CAP_NET_ADMIN`.

Le unit installate determinano le configurazioni runtime tramite variabili
d'ambiente come `WG_CLIENT_CONFIG`, `WG_CONFIG`, `WG_PROGRAM`,
`WG_MOCK_STATE` e `WG_MOCK_LOG`.

## Configurazione e stato

File principali:

```text
config/wg-auth.conf
config/wg-client-test-auth.conf
config/wg-manager.conf
```

Per vedere in un unico report unit systemd, configurazioni selezionate,
registry, utenti, mock state, socket e log:

```bash
python3 tools/wg_diagnostics.py
```

Opzioni utili:

```bash
python3 tools/wg_diagnostics.py --no-logs
python3 tools/wg_diagnostics.py --journal-lines 100
```

Gestione locale account/ownership:

```bash
python3 tools/manage_users.py --login-dir login create USER
python3 tools/manage_users.py --login-dir login delete USER
python3 tools/manage_users.py --login-dir login claim-peer USER PUBLIC_KEY
```

## Test

La suite corrente copre:

- OPAQUE e lifecycle account;
- state machine auth;
- parsing/activation client;
- secure session Python e JavaScript;
- replay, concurrency e cross-language vectors;
- peer CRUD e authorization;
- rollback/partial failure;
- ownership e reassignment;
- peer registry e IP registry;
- IPC reale client <-> auth per peer/admin/account RPC;
- API HTTPS client;
- mock WireGuard;
- flow E2E JavaScript.

Test Python:

```bash
pytest -v
```

E2E:

```bash
node tests/e2e/test_js_full_flow.mjs
node tests/e2e/test_js_user_lifecycle.mjs
node tests/frontend/test_secure_session_concurrency.test.mjs
```

## Documentazione automatica

`docs/ai/` contiene snapshot e documentazione generati meccanicamente.
Non va trattata come specifica normativa e non va modificata manualmente.

Gli snapshot principali sono:

```text
docs/ai/wg_auth_proto.md
docs/ai/wg_client_proto.md
docs/ai/wg_manager_proto.md
docs/ai/wg_all_proto.md
```

La documentazione sugli strumenti di analisi statica resta in:

```text
docs/comm-callgraph.md
docs/protocol-flow.md
docs/static-analysis.md
```

## Stato del progetto

Il backend di autenticazione/sessione/ownership/peer management è considerato
completo per questa fase ed è coperto dalla suite corrente.

Le attività successive sono mantenute in [TODO.md](TODO.md).
```
