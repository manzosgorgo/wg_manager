# `docs/wg-client-api.md`

## Metadata

- Path: `docs/wg-client-api.md`
- Language: `markdown`
- Lines: 318
- SHA256: `198d7ce19c186b629d5e19fcd7b52ec184941c9a72d63cac6d9f0b4823b6b684`

## Source

```markdown
# Prima classe: `WGClientAPI`

Qui sono d'accordo con te: **non facciamola ancora funzionare davvero**.

La prima versione deve essere quasi una carcassa strumentata.

Io la strutturerei concettualmente così:

### `WGClientAPI`

**Responsabilità:**

> Rappresenta l'API applicativa di `wg-client` e coordina autenticazione, parsing e dispatch delle richieste verso `WireGuardManager`.

### Stato interno

* host/listen address
* porta HTTPS
* `listen_path`
* riferimento a `WireGuardManager`
* riferimento a `SecureSession` — inizialmente non utilizzato
* server HTTP/HTTPS
* configurazione TLS

---

### Inizializzazione

`__init__`

Deve ricevere almeno:

* indirizzo di ascolto
* porta
* certificato server
* chiave server
* CA, se vogliamo mantenere mTLS
* `listen_path`
* riferimento al manager WireGuard

Per ora **non deve fare magie**: prepara semplicemente l'oggetto.

Log:

```text
WGClientAPI: initialized
```

---

### `start()`

Avvia il server HTTPS.

Log:

```text
WGClientAPI: start()
```

e successivamente:

```text
WGClientAPI: HTTPS server started
```

---

### `stop()`

Ferma il server.

Log:

```text
WGClientAPI: stop()
```

---

### `handle_request()`

Questa è la funzione centrale che hai descritto.

Concettualmente:

```text
ricevi request
       ↓
parse
       ↓
controlla metodo/path
       ↓
autenticazione
       ↓
dispatch
```

Per ora l'autenticazione sarà un semplice:

```text
TODO → SecureSession
```

Log:

```text
WGClientAPI: handle_request()
```

---

### `authenticate()`

Per ora **vuota**.

Sarà il punto in cui successivamente entrerà:

```text
SecureSession.verify_request()
```

Log:

```text
WGClientAPI: authenticate()
```

Per il momento restituisce semplicemente un risultato fittizio, oppure ancora meglio non autorizza operazioni reali.

---

### `status()`

Per ora:

```text
WGClientAPI: status()
```

e basta.

Più avanti:

```text
WGClientAPI
    ↓
WireGuardManager.status()
```

---

### `add_peer()`

Per ora:

```text
WGClientAPI: add_peer()
```

Più avanti riceverà i parametri validati e chiamerà:

```text
WireGuardManager.add_peer()
```

---

### `remove_peer()`

Stesso schema:

```text
WGClientAPI: remove_peer()
```

poi:

```text
WireGuardManager.remove_peer()
```

---

### `dispatch()`

Questa secondo me vale la pena averla separata da `handle_request()`.

`handle_request()` gestisce il **processo generale**:

```text
request
 ↓
parse
 ↓
auth
 ↓
dispatch
```

mentre `dispatch()` fa soltanto:

```text
GET /v1/status
        → status()

POST /v1/peers
        → add_peer()

DELETE /v1/peers/<key>
        → remove_peer()
```

Questa separazione ci renderà i test molto più semplici.

---

## E soprattutto: logging

Qui farei una piccola correzione rispetto alla tua idea.

**Non configurerei un nuovo `JournalHandler` dentro ogni file.**

Perché rischiamo di finire con:

```text
wg-client.py
    └── JournalHandler

wg-client-api.py
    └── JournalHandler

secure-session.py
    └── JournalHandler

wireguard-manager.py
    └── JournalHandler
```

e prima o poi ci troviamo con messaggi duplicati.

Invece farei:

```text
wg-client.py
    │
    └── configura logging
              │
              ▼
        JournalHandler
              │
              ▼
        logging globale
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
 SecureSession API  Manager
```

I singoli file fanno semplicemente:

```text
logger = logging.getLogger("wg-manager.secure-session")
logger = logging.getLogger("wg-manager.api")
logger = logging.getLogger("wg-manager.wireguard")
```

Così `wg-client.py` rimane **il punto di configurazione** del logging, mentre ogni modulo può produrre log.

E nel journal potremo distinguere:

```text
SYSLOG_IDENTIFIER=wg-client
```

con messaggi che riportano:

```text
wg-manager.api: ...
wg-manager.secure-session: ...
wg-manager.wireguard: ...
```

Questa secondo me è la soluzione definitiva.

---

### Quindi il primissimo lavoro concreto

Prima ancora di HTTPS, farei:

**1. `SecureSession` → aggiunta logging**

**2. definizione definitiva dell'envelope JSON**

**3. carcassa `WGClientAPI` con:**

```text
__init__
start
stop
handle_request
authenticate
dispatch
status
add_peer
remove_peer
```

tutte con log stupidi del tipo:

```text
WGClientAPI: add_peer()
```

e **zero WireGuard reale**.

A quel punto abbiamo una base perfetta per iniziare a costruire il server HTTPS pezzo per pezzo.
```
