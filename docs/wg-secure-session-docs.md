# WGSecureSession — Documentazione tecnica

Modulo: `src/wg_client/wg_secure_session.py`

## Panoramica

`WGSecureSession` implementa lo stato crittografico di una sessione autenticata per `wg_manager`. A partire da un segreto condiviso (`K_session`), stabilito in una fase di autenticazione precedente e mai trasmesso da questa classe, deriva le chiavi necessarie per **autenticare** (non cifrare) richieste e risposte HTTP-like tramite HMAC-SHA256, con protezione dai replay tramite contatori monotoni crescenti e nonce casuali.

**Importante**: questa classe fornisce solo *autenticazione dei messaggi* (integrità + provenienza), non confidenzialità. Il body della richiesta/risposta viene incluso nel calcolo del MAC solo come hash (SHA-256), non è cifrato.

---

## Costanti di classe

| Costante | Valore | Descrizione |
|---|---|---|
| `PROTOCOL_VERSION` | `b"wg_manager secure session v1"` | Stringa di dominio usata come `info` in HKDF, per binding a protocollo/versione |
| `session_id_size` | 16 byte | Lunghezza fissa del session id |
| `NONCE_SIZE` | 32 byte | Lunghezza del nonce casuale per ogni richiesta |
| `KEY_SIZE` | 32 byte | Lunghezza delle chiavi derivate (256 bit) |

---

## Costruttore

```python
WGSecureSession(k_session: bytes, session_id: bytes | None = None)
```

**Parametri**
- `k_session` (`bytes`, obbligatorio): segreto di sessione condiviso tra client e server. Deve essere `bytes` e lungo **almeno 32 byte** (256 bit).
- `session_id` (`bytes | None`, opzionale): identificatore di sessione a 16 byte. Se `None`, viene generato casualmente con `secrets.token_bytes(16)`. Se fornito, deve essere `bytes` di lunghezza esattamente 16.

**Eccezioni sollevate**
- `TypeError` — se `k_session` o `session_id` non sono `bytes`.
- `WGProtocolError` — se `k_session` è più corto di 32 byte, o se `session_id` non è lungo 16 byte.

**Cosa fa internamente**
1. Genera (o accetta) il `session_id`.
2. Deriva un `session_seed` tramite HKDF-SHA256, usando `session_id` come *salt* e `PROTOCOL_VERSION` come *info*, a partire da `k_session`.
3. Deriva due chiavi separate dal `session_seed` (sempre via HKDF, senza salt, con `info` = `PROTOCOL_VERSION + "|" + purpose`):
   - `_request_key` → per l'autenticazione delle richieste (`purpose = "request authentication"`)
   - `_response_key` → per l'autenticazione delle risposte (`purpose = "response authentication"`)
4. Inizializza i contatori anti-replay:
   - `_request_counter = 0` (lato client: prossimo contatore da usare per la creazione; lato server: ultimo contatore accettato)
   - `_last_response_counter = -1`

> Nota: client e server devono istanziare `WGSecureSession` con **lo stesso** `k_session` e **lo stesso** `session_id` per ottenere le stesse chiavi derivate (vedi test `test_same_session_derives_same_id`).

---

## Schema di derivazione delle chiavi

```
k_session (≥32 byte, segreto condiviso)
        │
        ▼  HKDF-SHA256(salt=session_id, info=PROTOCOL_VERSION)
   session_seed (32 byte)
        │
        ├──▶ HKDF-SHA256(salt=None, info=PROTOCOL_VERSION|"request authentication")  → request_key
        │
        └──▶ HKDF-SHA256(salt=None, info=PROTOCOL_VERSION|"response authentication") → response_key
```

Il `session_id` funge da salt nella prima derivazione: sessioni diverse (session_id diversi) con lo stesso `k_session` producono chiavi completamente diverse — questo è verificato da `test_different_sessions_have_different_ids`.

---

## Proprietà pubbliche

### `session_id -> bytes`
Restituisce il session id grezzo (16 byte).

### `session_id_b64 -> str`
Restituisce il session id codificato in Base64 URL-safe (usato nei payload di autenticazione).

---

## Autenticazione delle richieste

### `create_request_auth(method: str, path: str, body: bytes = b"") -> dict`

Genera i parametri di autenticazione per una nuova richiesta, lato **client/chiamante**.

**Parametri**
- `method`: verbo HTTP (es. `"GET"`, `"POST"`), come stringa.
- `path`: percorso della risorsa, come stringa.
- `body`: corpo della richiesta, come `bytes` (default vuoto).

**Comportamento**
1. Valida i tipi (`TypeError` se non corrispondono).
2. Incrementa `_request_counter` (quindi ogni chiamata usa un contatore univoco e crescente).
3. Genera un nonce casuale a 32 byte.
4. Costruisce il messaggio da autenticare (vedi [Formato dei messaggi](#formato-dei-messaggi-interni)).
5. Calcola `mac = HMAC-SHA256(request_key, message)`.

**Ritorna** un dizionario:
```python
{
    "session_id": "<base64url>",
    "counter": <int>,
    "nonce": "<base64url>",
    "mac": "<base64url>",
}
```

Questo dizionario va trasmesso insieme alla richiesta effettiva (es. come header o campo del payload).

---

### `verify_request(auth: dict, method: str, path: str, body: bytes = b"") -> bool`

Verifica l'autenticazione di una richiesta, lato **server/ricevente**.

**Controlli effettuati, in ordine**
1. `auth["session_id"]` deve corrispondere al `session_id_b64` di questa istanza → altrimenti `WGAuthenticationError("invalid session id")`.
2. `auth["counter"]` deve essere **strettamente maggiore** dell'ultimo contatore accettato (`_request_counter`) → altrimenti `WGReplayError("request counter replayed")`. Questo blocca sia il replay esatto sia il replay di contatori più vecchi.
3. Ricalcola il messaggio con gli stessi parametri (`method`, `path`, `body`, più `counter` e `nonce` ricevuti) e confronta il MAC ricevuto con quello atteso usando **confronto a tempo costante** (`hmac.compare_digest`) → se non coincide, `WGAuthenticationError("invalid request MAC")`. Questo rileva sia manomissioni del body/metodo/path sia chiavi non corrispondenti.
4. Se tutto è valido, aggiorna `_request_counter = counter` (avanzamento della finestra anti-replay) e ritorna `True`.

**Eccezioni**
- `WGAuthenticationError` — session id errato o MAC non valido (dati manomessi o chiave sbagliata).
- `WGReplayError` — contatore già visto o più vecchio di quello corrente.

> Nota sull'ordine dei controlli: il controllo del contatore avviene **prima** della verifica del MAC. Questo significa che un contatore duplicato/vecchio viene rifiutato come replay anche prima di verificare l'autenticità crittografica del messaggio.

---

## Autenticazione delle risposte

### `create_response_auth(request_auth: dict, status: int, body: bytes = b"") -> dict`

Genera i parametri di autenticazione per la risposta a una richiesta già verificata, lato **server**.

**Parametri**
- `request_auth`: il dizionario di auth della richiesta corrispondente (in particolare vengono riusati `counter` e `nonce` della richiesta).
- `status`: codice di stato della risposta (es. `200`), come `int`.
- `body`: corpo della risposta, come `bytes`.

**Comportamento**
- Riusa il `counter` e il `nonce` della richiesta originale (non ne genera di nuovi) → lega crittograficamente la risposta a quella specifica richiesta.
- Calcola `mac = HMAC-SHA256(response_key, message)` sul messaggio di risposta (vedi sotto).

**Ritorna**
```python
{
    "session_id": "<base64url>",
    "counter": <int>,      # uguale a request_auth["counter"]
    "mac": "<base64url>",
}
```

---

### `verify_response(auth: dict, request_auth: dict, status: int, body: bytes = b"") -> bool`

Verifica l'autenticazione di una risposta, lato **client**.

**Controlli effettuati, in ordine**
1. `auth["session_id"]` deve corrispondere al proprio `session_id_b64` → altrimenti `WGAuthenticationError("invalid session id")`.
2. `auth["counter"]` deve essere uguale a `request_auth["counter"]` (la risposta deve riferirsi esattamente alla richiesta attesa) → altrimenti `WGAuthenticationError("response counter does not match request")`.
3. Il counter deve essere **strettamente maggiore** di `_last_response_counter` → altrimenti `WGReplayError("response replayed")`.
4. Ricalcola il messaggio (riusando il `nonce` presente in `request_auth`, non in `auth` — la risposta non trasporta un proprio nonce) e confronta il MAC con confronto a tempo costante → altrimenti `WGAuthenticationError("invalid response MAC")`.
5. Se valido, aggiorna `_last_response_counter = counter` e ritorna `True`.

---

## Formato dei messaggi interni

I messaggi da autenticare sono costruiti concatenando i campi con `|` come separatore (tra `bytes`), dopo aver codificato in UTF-8 le stringhe e in ASCII i numeri, e sostituendo il body con il suo hash SHA-256 (per evitare messaggi enormi e per uniformità):

**Messaggio di richiesta** (`_request_message`):
```
session_id | counter (ascii) | nonce | method (utf-8) | path (utf-8) | SHA256(body)
```

**Messaggio di risposta** (`_response_message`):
```
session_id | counter (ascii) | nonce | status (ascii) | SHA256(body)
```

Da notare:
- Il `session_id` è incluso in entrambi i messaggi → lega ogni MAC a una sessione specifica.
- Il `nonce` della risposta è **quello della richiesta originale**, non uno nuovo: la risposta non genera un proprio nonce.
- L'uso di `|` come separatore tra campi di lunghezza variabile (es. `method`, `path`) potrebbe teoricamente creare ambiguità se un campo contenesse byte `|`; nella pratica HTTP metodo e path non contengono `|`, ma è un dettaglio implementativo da tenere presente se si estende il protocollo.

---

## Encoding

- `_b64(value: bytes) -> str`: Base64 URL-safe standard (`base64.urlsafe_b64encode`), per rendere i campi binari (session id, nonce, mac) trasportabili in JSON/testo.
- `_unb64(value: str) -> bytes`: decodifica inversa.

---

## Eccezioni utilizzate

Definite in `src/wg_client/wg_client_errors.py` (non incluso in questo estratto, ma usato dal modulo):

| Eccezione | Quando viene sollevata |
|---|---|
| `WGProtocolError` | Parametri di costruzione non validi (`k_session` troppo corto, `session_id` di lunghezza errata) |
| `WGAuthenticationError` | Session id non corrispondente, MAC di richiesta/risposta non valido |
| `WGReplayError` | Contatore di richiesta o risposta già usato/non crescente (replay) |

---

## Modello di sicurezza — riepilogo

| Proprietà | Garantita? | Come |
|---|---|---|
| Integrità della richiesta/risposta | ✅ | HMAC-SHA256 su metodo, path, status e hash del body |
| Autenticità (provenienza dal possessore di `K_session`) | ✅ | Chiavi derivate da `K_session` via HKDF, mai trasmesse |
| Anti-replay richieste | ✅ | Contatore monotono crescente, verificato lato server |
| Anti-replay risposte | ✅ | Contatore monotono crescente, verificato lato client |
| Binding risposta↔richiesta | ✅ | Il counter e il nonce della risposta devono coincidere con quelli della richiesta |
| Confidenzialità del body | ❌ | Il body non è cifrato, solo hashato per il MAC |
| Resistenza a timing attack sul confronto MAC | ✅ | `hmac.compare_digest` |

---

## Esempio d'uso (basato sui test)

```python
from src.wg_client.wg_secure_session import WGSecureSession

k_session = get_shared_secret()  # >= 32 byte, stabilito in fase di auth
session_id = b"..."              # 16 byte, condiviso tra le parti

# Ogni parte istanzia la propria sessione con lo stesso K_session/session_id
client = WGSecureSession(k_session, session_id)
server = WGSecureSession(k_session, session_id)

# --- Client: crea ed invia una richiesta ---
auth = client.create_request_auth("POST", "/api/test", b'{"command":"hello"}')
# invia `auth` + method + path + body al server

# --- Server: verifica la richiesta ricevuta ---
server.verify_request(auth, "POST", "/api/test", b'{"command":"hello"}')  # True, o solleva eccezione

# --- Server: crea la risposta autenticata ---
response_auth = server.create_response_auth(auth, 200, b"OK")

# --- Client: verifica la risposta ricevuta ---
client.verify_response(response_auth, auth, 200, b"OK")  # True, o solleva eccezione
```

---

## Comportamenti da tenere presenti (edge case)

- **Un solo contatore di richiesta condiviso lato server**: `_request_counter` funge sia da "prossimo contatore da usare" (lato che crea richieste) sia da "ultimo contatore accettato" (lato che verifica). Se la stessa istanza viene usata sia per creare sia per verificare richieste nella stessa sessione, i due usi condividono lo stesso contatore — nell'uso tipico client/server separati questo non è un problema, ma va considerato se si riusa la classe in modo bidirezionale sulla stessa istanza.
- **Ordine dei parametri di verifica**: `verify_request`/`verify_response` richiedono che il chiamante fornisca *esternamente* `method`/`path`/`body`/`status` attesi: la funzione non si fida di eventuali valori "dichiarati" nel payload, ricalcola tutto da zero — corretto per prevenire tampering.
- **Nessuna scadenza temporale**: il meccanismo anti-replay è basato solo su contatori monotoni, non ci sono timestamp o TTL; una sessione va quindi gestita/chiusa a un livello superiore (es. scadenza esplicita, rotazione di `k_session`).