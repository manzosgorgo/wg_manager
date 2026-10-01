# `README.md`

## Metadata

- Path: `README.md`
- Language: `markdown`
- Lines: 368
- SHA256: `20a4f11bcd714dbd5a8a52a595fd02c725c348d9e274f1b21297646b323fe6dc`

## Source

```markdown
# WireGuard Manager (`wg_manager`)

Sistema sicuro, modulare e isolato per la gestione dinamica del ciclo di vita di endpoint e peer WireGuard, basato su socket activation systemd, separazione dei privilegi a livello di processo e sessioni crittografiche anti-replay.

---

## 1. Panoramica del Progetto

`wg_manager` è un'infrastruttura backend progettata per consentire la configurazione e il provisioning dinamico di peer WireGuard con i massimi requisiti di sicurezza. L'architettura adotta il principio del privilegio minimo (*least privilege*) e della separazione dei compiti (*separation of concerns*):

- **Isolamento dei Privilegi**: I servizi aperti verso l'esterno o che gestiscono le sessioni client non possiedono capacità di rete avanzate. Solo il controller di backend (`wg_manager`) detiene la capability Linux `CAP_NET_ADMIN`.
- **Istanze per-sessione Effimere**: L'API del client (`wg_client`) viene creata dinamicamente su richiesta da `systemd` tramite socket activation Unix IPC (`Accept=yes`). Ogni sessione client opera in un processo dedicato, isolato, con un percorso URL casuale (`listen_path`) e un timer di scadenza rigoroso.
- **Crittografia a Livelli Multipli**:
  - Trasporto sicuro con **TLS 1.3** e mutua autenticazione certificati (**mTLS**).
  - Autenticazione applicativa a livello di messaggio tramite **`WGSecureSession`**, che implementa HKDF-SHA256, HMAC-SHA256, nonce crittografici e contatori anti-replay.

---

## 2. Architettura dei Servizi e Ciclo di Vita (Lifecycle)

### Schema Architetturale

```text
 ┌────────────────┐
 │     Client     │ (Browser / App Mobile)
 └───────┬────────┘
         │ 1. Autenticazione (es. OPAQUE / TLS)
         ▼
 ┌───────────────────────────┐
 │       wg_auth             │ (Endpoint esterno di autenticazione)
 └───────────┬───────────────┘
             │ 2. Pacchetto di Attivazione JSON
             ▼
 ┌───────────────────────────┐
 │   wg-client-test.socket   │ (AF_UNIX IPC, Accept=yes)
 └───────────┬───────────────┘
             │ 3. Istanziamento per-sessione (StandardInput=socket)
             ▼
 ┌───────────────────────────┐
 │   wg-client-test@.service │ ◄── Processo wg_client.py
 │                           │     - Valida activation packet
 │                           │     - Inizializza WGClientAPI & bind() TLS 1.3
 │                           │     - Risponde ACTIVATION_RESULT (OK) su IPC
 │                           │     - Notifica systemd READY=1
 └───────────┬───────────────┘     - Avvia timer di sessione (timeout)
             │
             │ 4. Richieste REST autenticate HTTPS
             │    (GET /v1/status, PUT /v1/peers/<pk>, DELETE /v1/peers/<pk>)
             ▼
 ┌───────────────────────────┐
 │  WGClientAPIHandler       │
 └───────────┬───────────────┘
             │ 5. Inoltro HTTPS mTLS (WGControllerClient)
             ▼
 ┌───────────────────────────┐
 │ wg-controller-test.socket │ (127.0.0.1:9443)
 └───────────┬───────────────┘
             │
             ▼
 ┌───────────────────────────┐
 │   wg_manager.py           │ (Esegue con CAP_NET_ADMIN)
 └───────────┬───────────────┘
             │ 6. Configurazione kernel o mock
             ▼
 ┌───────────────────────────┐
 │   WireGuard (wg0 / mock)  │
 └───────────────────────────┘
```

### Ciclo di Vita della Sessione (`Lifecycle`)

1. **Attivazione IPC**: `wg_auth` riceve l'autenticazione dell'utente, stabilisce una chiave segreta di sessione `k_session` e si connette al socket Unix `/run/wg_manager/wg-client-test.sock`.
2. **Creazione Servizio**: `systemd` avvia una nuova istanza `wg-client-test@<id>.service`, collegando il socket Unix direttamente allo standard input/output del processo `wg_client.py`.
3. **Validazione e Bind**: `wg_client.py` legge il pacchetto di attivazione JSON, valida i campi crittografici, le scadenze temporali e il `listen_path`. Successivamente effettua il `bind()` e l'inizializzazione TLS del server HTTPS (`WGClientAPI`).
4. **Ack e Ready**: Solo ad avvio e bind completati con successo, `wg_client` invia il messaggio `ACTIVATION_RESULT: {"type":"ACTIVATION_RESULT","status":"OK",...}` sul socket IPC e invia `READY=1` a systemd tramite `sd_notify`.
5. **Sessione Attiva**: Il client comunica direttamente via HTTPS con `WGClientAPIHandler` sul percorso dedicato `https://<host>:<port><listen_path>/v1/...`.
6. **Inoltro al Controller**: Le operazioni sui peer vengono validate (subnet, formato chiavi X25519) e inoltrate tramite client mTLS a `wg_manager.py`.
7. **Scadenza e Shutdown**: Un timer asincrono (`threading.Timer`) monitora la durata della sessione. Alla scadenza del `timeout` (o su interruzione di segnale), il server HTTPS viene arrestato ordinatamente (`stop()`), viene inviato `STOPPING=1` a systemd e il socket IPC viene chiuso.

---

## 3. Struttura dei File e delle Directory

```text
wg_manager/
├── src/
│   ├── wg_client/                      # Componenti del client e dell'API per-sessione
│   │   ├── __init__.py
│   │   ├── wg_client.py                # Entry point per-sessione: gestione IPC, lifecycle, timer, systemd notify
│   │   ├── wg_client_API.py            # Lifecycle del server HTTPS (WGClientHTTPServer, bind, TLS 1.3 mTLS, serve, stop)
│   │   ├── wg_client_API_handler.py    # Handler HTTP REST (BaseHTTPRequestHandler) per routing e parsing endpoint
│   │   ├── wg_client_config.py         # Parsing della configurazione INI per wg_client
│   │   ├── wg_client_errors.py         # Gerarchia delle eccezioni (WGError, WGProtocolError, WGAPIError, ecc.)
│   │   ├── wg_controller_client.py     # Client HTTPS mTLS verso wg_manager (WGControllerClient e WGCClientClient)
│   │   └── wg_secure_session.py        # Stato crittografico: HKDF-SHA256, HMAC-SHA256, nonce, contatori anti-replay
│   │
│   └── wg_manager/
│       └── wg_manager.py               # Controller WireGuard privileged: parsing HTTP, policy IP e invocazione wg/mock
│
├── config/                             # File di configurazione INI
│   ├── wg-client-test.conf             # Configurazione per wg_client (porte, certificati, controller)
│   ├── wg-manager.conf                 # Configurazione base per il controller wg_manager
│   ├── wg-manager-realtest.conf        # Configurazione per test reali su interfaccia wg0
│   └── wg-manager-captest.conf         # Configurazione per test di capability e policy
│
├── systemd/                            # Definizioni dei servizi e socket systemd
│   ├── wg-client-test.socket           # Socket activation Unix domain stream per wg_client
│   ├── wg-client-test@.service         # Unit template istanziata per ogni connessione/sessione IPC
│   ├── wg-controller-test.socket       # Socket activation TCP (127.0.0.1:9443) per wg_manager
│   ├── wg-controller-test@.service     # Unit template istanziata per ogni richiesta al controller
│   └── install/                        # Script di installazione dei servizi nel sistema
│       ├── install-client-service.sh
│       └── install-server-service.sh
│
├── cert/ / tls/                        # Certificati X.509 e chiavi per TLS 1.3 / mTLS
│   ├── ca.crt                          # Certificate Authority condivisa
│   ├── server.crt / server.key         # Certificato e chiave privata del server
│   └── client.crt / client.key         # Certificato e chiave privata del client mTLS
│
├── mock/                               # Script di simulazione per test e sviluppo locale
│   └── mock                            # Mock dell'eseguibile /usr/bin/wg (gestisce stato in /tmp/mock-state.txt)
│
├── docs/                               # Documentazione di dettaglio e specifiche architetturali
│   ├── architettura-completa.md        # Specifica approfondita dell'architettura e dei flussi
│   ├── struttura.md                    # Nomenclatura, ruoli dei componenti e convenzioni di progetto
│   ├── wg-client-api.md                # Specifiche delle API del client
│   └── roadmap.md                      # Roadmap e checklist di avanzamento implementativo
│
├── tests/                              # Suite di test automatizzati (pytest)
│   ├── client/
│   │   ├── test_wg_client_lifecycle.py # Test completi di parsing activation packet, lifecycle, timeout e HTTPS
│   │   ├── test_secure_session.py      # Test di derivazione chiavi, validazione HMAC, anti-tampering e anti-replay
│   │   ├── test_client.py              # Test funzionali end-to-end su WGCClientClient e API
│   │   ├── test_client_API.py          # Runner interattivo standalone per WGClientAPI
│   │   └── test_wg_client_activator.py # Script CLI per simulare l'attivazione IPC via socket Unix
│   └── pyproject.toml                  # Configurazione del build system e di pytest
└── README.md                           # Questo documento di riepilogo
```

---

## 4. Specifiche del Protocollo

### 4.1 Protocollo IPC di Attivazione (`wg_auth` ➔ `wg_client`)

La comunicazione avviene su socket Unix `AF_UNIX` (`/run/wg_manager/wg-client-test.sock`). Il pacchetto di attivazione è un oggetto JSON su una singola riga terminata da newline (`\n`), di dimensione massima 64 KB.

#### Pacchetto di Attivazione (Richiesta)
```json
{
  "protocol_version": 1,
  "session_id": "7f3a91c2e8b44d17a6f05c9b31de8247",
  "k_session": "b7e4a2c91f6d08359a31c7e4b25f608d4c8e1a73f0b692de5a17c3f84e29b601",
  "client_id": "android-test-client",
  "timeout": 1800,
  "created_at": 1800000000,
  "listen_path": "/api/7f3a91c2e8b44d17/9c71e4a2f6b83d10"
}
```

- `protocol_version` (*int*): Versione del protocollo (attualmente `1`).
- `session_id` (*hex string*): Identificatore univoco di sessione a 128 bit (16 byte, 32 caratteri hex).
- `k_session` (*hex string*): Chiave simmetrica segreta stabilita in fase di autenticazione (almeno 32 byte, 64 caratteri hex).
- `client_id` (*string*): Identificativo testuale non vuoto del client.
- `timeout` (*int*): Durata massima della sessione in secondi ($1 \le \text{timeout} \le 86400$).
- `created_at` (*int*): Timestamp Unix di generazione del pacchetto (tolleranza clock skew $\pm 30\text{s}$).
- `listen_path` (*string*): Prefisso URL su cui risponderà l'API (es. `/api/<segmento_1>/<segmento_2>`).

#### Risposta di Attivazione (`ACTIVATION_RESULT`)
- In caso di successo (dopo il corretto bind HTTPS):
  ```json
  {
    "type": "ACTIVATION_RESULT",
    "status": "OK",
    "session_id": "7f3a91c2e8b44d17a6f05c9b31de8247",
    "listen_path": "/api/7f3a91c2e8b44d17/9c71e4a2f6b83d10",
    "expires_at": 1800001800
  }
  ```
- In caso di errore (validazione pacchetto o bind fallito):
  ```json
  {
    "type": "ACTIVATION_RESULT",
    "status": "ERROR",
    "error": "failed to initialize HTTPS API: [Errno 98] Address already in use"
  }
  ```

---

### 4.2 Protocollo di Sicurezza Applicativa (`WGSecureSession`)

`WGSecureSession` garantisce confidenzialità dell'identificativo, autenticità dei messaggi e protezione da manomissioni e attacchi di replay:

1. **Derivazione delle Chiavi**:
   $$\text{SessionSeed} = \text{HKDF-SHA256}(\text{key}=K_{\text{session}}, \text{salt}=\text{SessionID}, \text{info}=\text{"wg\_manager secure session v1"})$$
   $$\text{Key}_{\text{request}} = \text{HKDF-SHA256}(\text{key}=\text{SessionSeed}, \text{info}=\text{"wg\_manager secure session v1|request authentication"})$$
   $$\text{Key}_{\text{response}} = \text{HKDF-SHA256}(\text{key}=\text{SessionSeed}, \text{info}=\text{"wg\_manager secure session v1|response authentication"})$$

2. **Dati di Autenticazione della Richiesta**:
   - `session_id_b64`: Base64 del `session_id`.
   - `counter`: Intero strettamente crescente per richiesta.
   - `timestamp`: Timestamp Unix (controllo finestra temporale $\pm 30\text{s}$).
   - `nonce_b64`: Nonce casuale CSPRNG a 256 bit (32 byte in Base64).
   - `mac_b64`: $\text{HMAC-SHA256}(\text{Key}_{\text{request}}, \text{SessionID} \parallel \text{Counter} \parallel \text{Timestamp} \parallel \text{Nonce} \parallel \text{Method} \parallel \text{Path} \parallel \text{SHA256}(\text{Body}))$.

3. **Autenticazione della Risposta**:
   - $\text{Response-MAC} = \text{HMAC-SHA256}(\text{Key}_{\text{response}}, \text{SessionID} \parallel \text{Counter} \parallel \text{Nonce} \parallel \text{Status} \parallel \text{SHA256}(\text{Body}))$.

---

### 4.3 Specifiche API REST HTTPS (`WGClientAPI`)

Tutte le chiamate sono esposte sotto il prefisso dinamico configurato in `listen_path`.

#### 1. Stato del Gateway
- **Metodo / Path**: `GET <listen_path>/v1/status`
- **Descrizione**: Restituisce lo stato dell'interfaccia e l'elenco dei peer registrati.
- **Risposta (200 OK)**:
  ```json
  {
    "interface": "wg0",
    "peers": [
      {
        "public_key": "x5TFq2PZmM+kYwQk...=",
        "endpoint": "198.51.100.1:51820",
        "allowed_ips": ["10.8.0.2/32"],
        "latest_handshake": "1710000000",
        "transfer_rx": "1048576",
        "transfer_tx": "2097152"
      }
    ]
  }
  ```

#### 2. Registrazione / Aggiornamento Peer
- **Metodo / Path**: `PUT <listen_path>/v1/peers/<public_key_b64>`
- **Body JSON**:
  ```json
  {
    "allowed_ip": "10.8.0.2/32"
  }
  ```
- **Risposta (200 OK)**:
  ```json
  {
    "status": "ok",
    "public_key": "x5TFq2PZmM+kYwQk...=",
    "allowed_ip": "10.8.0.2/32"
  }
  ```

#### 3. Rimozione Peer
- **Metodo / Path**: `DELETE <listen_path>/v1/peers/<public_key_b64>`
- **Risposta (200 OK)**:
  ```json
  {
    "status": "ok",
    "public_key": "x5TFq2PZmM+kYwQk...="
  }
  ```

#### Formato Standard degli Errori JSON
In caso di errore HTTP (es. 400, 404, 405, 500, 502):
```json
{
  "timestamp": "2026-09-24T20:22:00.000000+00:00",
  "status": 404,
  "error": "Not Found",
  "message": "resource not found",
  "path": "/api/test/v1/unknown"
}
```

---

### 4.4 Specifiche Controller WireGuard (`wg_manager`)

Il servizio `wg_manager.py` riceve richieste tramite socket TCP locale protetto da mTLS (default `127.0.0.1:9443`):
- `GET /v1/status`: Esegue `wg show <if> dump` e restituisce i dati strutturati dei peer.
- `POST /v1/peers`: Valida la chiave pubblica a 32 byte e la subnet (`policy.vpn_network`), quindi esegue `wg set <if> peer <pk> allowed-ips <ip>`.
- `DELETE /v1/peers/<pk>`: Esegue `wg set <if> peer <pk> remove`.

---

## 5. Configurazione

I file di configurazione utilizzano la sintassi standard INI.

### Esempio: `config/wg-client-test.conf`
```ini
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
```

### Esempio: `config/wg-manager.conf`
```ini
[manager]
interface = wg0

[tls]
server_cert = /home/main/Desktop/wg_manager/cert/server.crt
server_key = /home/main/Desktop/wg_manager/cert/server.key
client_ca = /home/main/Desktop/wg_manager/cert/ca.crt

[policy]
vpn_network = 10.8.0.0/24
```

---

## 6. Sicurezza e Hardening con systemd

I servizi systemd inclusi in `systemd/` applicano le direttive di hardening raccomandate da Linux Security:

- **`Type=notify`** con integrazione nativa di `sd_notify` (`READY=1`, `STOPPING=1`, `STATUS=...`).
- **`NoNewPrivileges=yes`**: Previene l'elevazione dei privilegi tramite setuid/setgid.
- **`ProtectSystem=strict`** e **`ProtectKernelTunables=yes`**: Monta il filesystem di sistema in sola lettura e blocca la manipolazione di sysctl.
- **`PrivateTmp=yes`**: Crea uno spazio dei nomi isolato per `/tmp`.
- **`CapabilityBoundingSet=CAP_NET_ADMIN`** e **`AmbientCapabilities=CAP_NET_ADMIN`**: Assegnate esclusivamente al servizio di gestione `wg-controller-test@.service`.

---

## 7. Esecuzione dei Test e Strumenti di Sviluppo

### Prerequisiti
- Python 3.11+
- `cryptography`, `pytest`

### Eseguire i Test Automatici
Per eseguire l'intera suite di test unitari e di integrazione:

```bash
pytest tests/client/
```

### Test di Attivazione Socket Manuale
Per simulare il passaggio del pacchetto di attivazione da `wg_auth` al socket Unix:

```bash
python3 tests/client/test_wg_client_activator.py --socket /run/wg_manager/wg-client-test.sock --timeout 1800
```

### Test Funzionale API e Controller
Per verificare le operazioni CRUD dei peer contro un'istanza API attiva:

```bash
python3 tests/client/test_client.py --host 127.0.0.1 --port 9444 --peer-ip 10.8.0.2/32
```
```
