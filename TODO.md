from src.wg_client import wg_client_IPC_control_loop

# TODO list — `wg_manager`

Ho esaminato il codice che hai riportato e l'ho confrontato con il `README.md`, tenendo conto dell'architettura che hai scelto: `wg_auth` per l'autenticazione, `wg_client` per la gestione delle sessioni HTTPS e `wg_manager` come controller privilegiato.

La situazione è abbastanza chiara: **hai già realizzato una parte consistente dell'infrastruttura, ma il protocollo applicativo non è ancora collegato al server HTTP**.

In particolare, distinguerei tre livelli di lavoro:

1. **Completare `wg_auth` e il protocollo di attivazione.**
2. **Integrare `WGSecureSession` nell'API HTTPS**, in modo che le richieste siano effettivamente autenticate a livello applicativo.
3. **Completare e verificare l'integrazione end-to-end**, dal browser fino al controller WireGuard.

Ci sono inoltre alcune discrepanze fra il README e il codice attuale, oltre ad alcuni problemi di concorrenza e di gestione delle sessioni che conviene affrontare prima di considerare conclusa l'implementazione.

Di seguito trovi una TODO list organizzata per priorità, distinguendo le funzionalità mancanti dai controlli di sicurezza e dalle attività di rifinitura.


---

## 1. Stato attuale dei componenti

| Componente           | Stato                        | Osservazioni                                                                                                            |
| -------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `wg_client.py`       | Parzialmente implementato    | Attivazione IPC, validazione iniziale, bind HTTPS, timer e notifiche systemd già presenti.                              |
| `WGClientAPI`        | Parzialmente implementato    | Lifecycle HTTPS presente; autenticazione e dispatch non implementati.                                                   |
| `WGClientAPIHandler` | Parzialmente implementato    | Routing di base presente, ma le richieste non sono ancora autenticate.                                                  |
| `WGSecureSession`    | Implementato parzialmente    | Derivazione delle chiavi, HMAC, nonce e contatori presenti; integrazione HTTP assente e alcune proprietà da correggere. |
| `WGControllerClient` | Implementato                 | Comunicazione HTTPS mTLS verso il controller già presente.                                                              |
| `WGClientClient`    | Implementato parzialmente    | Client HTTP verso l'API per-sessione presente, ma non utilizza `WGSecureSession`.                                       |
| `wg_manager.py`      | Già sviluppato separatamente | Controller privilegiato già presente nel progetto; da verificare l'integrazione con il nuovo client.                    |
| `wg_auth`            | Da implementare              | Mancano il servizio di autenticazione e il coordinamento dell'attivazione.                                              |
| Frontend             | Da integrare                 | Deve eseguire l'autenticazione, ricevere i dati di attivazione e gestire le operazioni sui peer.                        |
| Test end-to-end      | Da completare                | Occorre verificare l'intero percorso, dall'autenticazione fino alle operazioni sul controller.                          |

---

# 2. TODO list principale

## FASE A — Completamento di `WGSecureSession`

**Priorità: critica.**

Prima di collegare l'autenticazione al server HTTP, conviene stabilizzare il protocollo crittografico.

### A1. Definire il formato definitivo dei messaggi autenticati

* [ ] Definire un formato canonico per i metadati di autenticazione.
* [ ] Stabilire i nomi definitivi degli header HTTP, per esempio:

  * `X-WG-Session-ID`
  * `X-WG-Counter`
  * `X-WG-Nonce`
  * `X-WG-MAC`
* [ ] Decidere se utilizzare un timestamp nelle richieste.
* [ ] Definire la codifica esatta di ogni campo prima del calcolo HMAC.
* [ ] Definire quali dati vengono autenticati: metodo HTTP, path, query string, body e altri eventuali metadati.
* [ ] Definire il formato dell'autenticazione della risposta.

**Nota:** il README descrive un timestamp nell'autenticazione delle richieste, ma l'implementazione corrente di `WGSecureSession` non lo include. Bisogna scegliere una specifica unica e allineare codice e documentazione.

### A2. Correggere e completare la gestione dei contatori

* [ ] Separare chiaramente il contatore delle richieste inviate da quello delle richieste ricevute.
* [ ] Definire il comportamento in caso di richieste concorrenti.
* [ ] Garantire che l'aggiornamento del contatore sia atomico.
* [ ] Gestire correttamente i contatori delle risposte.
* [ ] Definire il comportamento in caso di contatore esaurito.
* [ ] Stabilire se una richiesta autenticata ma fallita a livello applicativo consuma comunque il proprio contatore.

**Attenzione a un dettaglio concreto:** `WGSecureSession` utilizza `_request_counter` sia in `create_request_auth()` sia in `verify_request()`.

Questo funziona soltanto se il modello di utilizzo è definito con attenzione. Se il client e il server utilizzano istanze distinte, i rispettivi contatori devono avere responsabilità separate. Se più thread condividono un'istanza, gli incrementi e le verifiche devono inoltre essere sincronizzati.

### A3. Rafforzare la serializzazione crittografica

* [ ] Evitare serializzazioni ambigue dei campi autenticati.
* [ ] Utilizzare una codifica non ambigua, ad esempio campi con lunghezza esplicita o una serializzazione canonica rigorosamente definita.
* [ ] Verificare il formato e la lunghezza del nonce ricevuto.
* [ ] Verificare il formato e la lunghezza del MAC ricevuto.
* [ ] Gestire esplicitamente gli errori di decodifica Base64.
* [ ] Verificare che il confronto dei MAC avvenga sempre con `hmac.compare_digest()`.
* [ ] Definire il comportamento in caso di MAC non valido, session ID errato e replay.

### A4. Completare l'interfaccia pubblica della sessione

* [ ] Stabilire quali metodi devono essere pubblici.
* [ ] Separare le operazioni del client da quelle del server, se necessario.
* [ ] Definire un'interfaccia uniforme per creare e verificare richieste e risposte.
* [ ] Documentare il ciclo di vita della sessione crittografica.
* [ ] Aggiungere test per richieste concorrenti e messaggi malformati.

### A5. Test crittografici

* [ ] Testare la derivazione delle chiavi con vettori di test noti.
* [ ] Verificare che una modifica del metodo HTTP invalidi il MAC.
* [ ] Verificare che una modifica del path invalidi il MAC.
* [ ] Verificare che una modifica del body invalidi il MAC.
* [ ] Verificare che una modifica del contatore invalidi il MAC.
* [ ] Verificare il rifiuto dei replay.
* [ ] Verificare che una risposta non possa essere associata a una richiesta differente.
* [ ] Verificare che sessioni differenti non possano autenticare reciprocamente i propri messaggi.

---

## FASE B — Integrazione di `WGSecureSession` nell'API HTTPS

**Priorità: critica.**

Questa è probabilmente la parte più importante del lavoro immediatamente successivo.

Attualmente `WGClientAPI` riceve una sessione:

```python
api = WGClientAPI(cfg, activation["listen_path"], session)
```

ma il relativo handler non la utilizza per autenticare le richieste.

Di conseguenza, l'autenticazione applicativa descritta nel README non è ancora operativa.

### B1. Collegare la sessione all'handler

* [ ] Rendere disponibile `WGSecureSession` all'interno di `WGClientAPIHandler`.
* [ ] Definire un metodo comune per autenticare le richieste HTTP.
* [ ] Definire un metodo comune per autenticare le risposte.
* [ ] Evitare di duplicare la logica crittografica nei vari `do_GET()`, `do_PUT()` e `do_DELETE()`.
* [ ] Definire il comportamento per richieste prive degli header di autenticazione.
* [ ] Definire il comportamento per richieste con autenticazione malformata.
* [ ] Definire il comportamento per sessioni scadute.
* [ ] Assicurarsi che le risposte di errore siano coerenti con il protocollo.

### B2. Introdurre un dispatch centralizzato

Attualmente:

```python
def authenticate(self):
    log.debug("Authenticating WGClientAPI")

def dispatch(self):
    log.debug("Dispatching WGClientAPI")
```

sono ancora stub.

* [ ] Implementare `authenticate()`.
* [ ] Implementare `dispatch()`.
* [ ] Definire una pipeline comune per tutte le richieste.
* [ ] Separare l'autenticazione dal routing.
* [ ] Separare il routing dalla logica applicativa.
* [ ] Definire una gestione uniforme delle eccezioni.

Una possibile organizzazione logica è:

```text
Richiesta HTTP
      │
      ▼
Parsing e validazione HTTP
      │
      ▼
Verifica sessione e autenticazione
      │
      ▼
Controllo autorizzazioni
      │
      ▼
Dispatch endpoint
      │
      ▼
Esecuzione operazione
      │
      ▼
Autenticazione della risposta
      │
      ▼
Risposta HTTP
```

Non è necessario realizzare tutto in un unico metodo: l'importante è che ogni endpoint attraversi la stessa pipeline di sicurezza.

### B3. Integrare l'autenticazione nei metodi HTTP

* [ ] `GET /v1/status`: verificare la richiesta prima di interrogare il controller.
* [ ] `PUT /v1/peers/<pk>`: verificare la richiesta prima di aggiungere o aggiornare un peer.
* [ ] `DELETE /v1/peers/<pk>`: verificare la richiesta prima di rimuovere un peer.
* [ ] Definire esplicitamente il comportamento di `POST`, attualmente gestito da uno stub che risponde sempre `200 OK`.
* [ ] Garantire che gli endpoint non implementati restituiscano un errore coerente.
* [ ] Autenticare le risposte, comprese quelle di errore, secondo la specifica definitiva.

**Risultato atteso:** nessuna operazione applicativa deve essere eseguita prima che la richiesta abbia superato i controlli di autenticazione e autorizzazione previsti.

---

## FASE C — Implementazione di `wg_auth`

**Priorità: critica.**

Questo componente dovrà diventare il punto di ingresso del protocollo di autenticazione e il responsabile della creazione delle sessioni client.

### C1. Definire l'architettura del servizio

* [ ] Definire il ruolo preciso di `wg_auth`.
* [ ] Stabilire come il frontend raggiunge il servizio.
* [ ] Definire il protocollo di autenticazione iniziale.
* [ ] Stabilire come viene generato o derivato `k_session`.
* [ ] Definire il formato del risultato dell'autenticazione.
* [ ] Definire la gestione degli errori.
* [ ] Definire la separazione dei privilegi del servizio.

### C2. Implementare il protocollo di autenticazione

Se mantieni l'orientamento già discusso verso OPAQUE:

* [ ] Selezionare e integrare un'implementazione OPAQUE appropriata.
* [ ] Definire il formato dei messaggi scambiati tra client e server.
* [ ] Implementare la registrazione delle credenziali, se prevista.
* [ ] Implementare il protocollo di autenticazione.
* [ ] Definire come viene derivata la chiave di sessione.
* [ ] Garantire che la chiave venga condivisa esclusivamente tra le parti autorizzate.
* [ ] Definire la gestione delle credenziali persistenti.
* [ ] Implementare il controllo degli errori e dei tentativi falliti.

OPAQUE è un elemento da integrare nel protocollo, non una funzionalità già presente nel codice mostrato.

### C3. Implementare il coordinamento dell'attivazione IPC

* [ ] Creare il client IPC verso il socket Unix di `wg_client`.
* [ ] Serializzare il pacchetto di attivazione JSON.
* [ ] Includere tutti i campi richiesti:

  * `protocol_version`
  * `session_id`
  * `k_session`
  * `client_id`
  * `timeout`
  * `created_at`
  * `listen_path`
* [ ] Applicare i limiti temporali previsti.
* [ ] Gestire gli errori di connessione e di scrittura.
* [ ] Leggere e validare `ACTIVATION_RESULT`.
* [ ] Gestire il caso in cui `wg_client` non riesca a inizializzare HTTPS.
* [ ] Gestire il caso in cui l'attivazione riesca ma la comunicazione IPC si interrompa.

### C4. Gestire lo stato delle sessioni

* [ ] Definire quali informazioni di sessione devono essere mantenute da `wg_auth`.
* [ ] Stabilire se e come vengono memorizzate le sessioni attive.
* [ ] Definire la gestione delle sessioni scadute.
* [ ] Definire la revoca delle sessioni.
* [ ] Definire il comportamento dopo un riavvio di `wg_auth`.
* [ ] Definire come evitare duplicazioni o attivazioni incoerenti.
* [ ] Stabilire come correlare una sessione autenticata alla corrispondente istanza `wg_client`.

---


## FASE D — Risolvere le criticità architetturali

**Priorità: alta.**

Questi punti emergono direttamente dal codice che hai incollato.

### D1. Gestire correttamente le istanze HTTPS per-sessione

Attualmente ogni istanza di `WGClientAPI` utilizza:

```python
self.host = config["api"]["host"]
self.port = config["api"]["port"]
```

e crea un proprio server TCP.

Questo introduce una criticità: **due istanze non possono normalmente effettuare il bind sullo stesso indirizzo e sulla stessa porta**.

Il `listen_path` dinamico non risolve il problema, perché viene interpretato a livello HTTP e non modifica l'indirizzo di bind.

* [ ] Decidere se utilizzare una porta distinta per ogni sessione.
* [ ] In alternativa, valutare un listener HTTPS condiviso con routing verso le sessioni.
* [ ] Se si mantiene un listener condiviso, definire come associare ogni richiesta alla corretta sessione.
* [ ] Definire la gestione delle collisioni.
* [ ] Verificare il comportamento con più sessioni contemporanee.
* [ ] Verificare la chiusura delle sessioni senza interrompere quelle ancora attive.

La scelta deve essere coerente con il modello di isolamento per-sessione che hai descritto nel README.

### D2. Rendere sicuro il lifecycle concorrente

`WGClientHTTPServer` deriva da `ThreadingHTTPServer`.

Questo significa che più richieste possono essere gestite contemporaneamente.

* [ ] Definire la sincronizzazione dello stato di `WGSecureSession`.
* [ ] Verificare le condizioni di race sui contatori.
* [ ] Definire il comportamento durante lo shutdown con richieste ancora in corso.
* [ ] Verificare che il timer non possa provocare stati incoerenti.
* [ ] Verificare che le operazioni sul controller non possano lasciare la sessione in uno stato parzialmente aggiornato.
* [ ] Definire se le operazioni sui peer possono essere eseguite contemporaneamente.

### D3. Completare la gestione del timeout HTTP

Nel codice è presente:

```python
class WGClientAPIHandler(http.server.BaseHTTPRequestHandler):
    timeout = 30
```

Non darei per scontato che questa assegnazione, da sola, imponga un timeout di 30 secondi a tutte le operazioni di lettura della connessione.

* [ ] Verificare esplicitamente il timeout delle connessioni accettate.
* [ ] Proteggere la lettura del body da client che inviano dati lentamente.
* [ ] Definire il comportamento per richieste incomplete.
* [ ] Definire il comportamento per connessioni interrotte.
* [ ] Verificare il limite `MAX_BODY_SIZE`.
* [ ] Gestire correttamente richieste con `Content-Length` assente o non valido.

### D4. Rafforzare il parsing HTTP

* [ ] Verificare che il metodo HTTP sia consentito per ciascun endpoint.
* [ ] Verificare il formato del `Content-Type`.
* [ ] Definire la gestione di `Transfer-Encoding`.
* [ ] Definire la gestione di richieste con header duplicati o malformati.
* [ ] Validare il JSON in ingresso secondo uno schema preciso.
* [ ] Validare `allowed_ip` prima di inoltrarlo al controller.
* [ ] Validare il formato della chiave pubblica.
* [ ] Definire la gestione di path non validi e caratteri percent-encoded.
* [ ] Uniformare le risposte HTTP di errore.

La validazione della subnet e delle chiavi deve essere coerente con le policy applicate dal controller: non bisogna fare affidamento esclusivamente sui controlli del frontend.

---

## FASE E — Completamento del client HTTPS

**Priorità: alta.**

Il file `wg_controller_client.py` contiene già una buona parte della comunicazione HTTPS, ma il client diretto verso `wg_client` deve essere integrato con il protocollo di sessione.

### E1. Completare `WGClientClient`

* [ ] Integrare `WGSecureSession`.
* [ ] Generare gli header di autenticazione per ogni richiesta.
* [ ] Autenticare il metodo, il path e il body secondo la specifica definitiva.
* [ ] Verificare l'autenticazione delle risposte.
* [ ] Gestire i contatori delle richieste.
* [ ] Gestire le risposte di errore.
* [ ] Gestire le sessioni scadute.
* [ ] Definire il comportamento dopo un errore di rete.

### E2. Uniformare le classi client

* [ ] Chiarire la distinzione fra `WGControllerClient` e `WGClientClient`.
* [ ] Valutare una nomenclatura più esplicita, per esempio `WGControllerClient` e `WGClientAPIClient`.
* [ ] Correggere il nome attuale `WGClientClient`, se non è intenzionale.
* [ ] Evitare di duplicare codice HTTP/TLS non necessario.
* [ ] Separare gli errori del controller dagli errori dell'API client.
* [ ] Definire un formato uniforme per le eccezioni.

**Nota:** al momento `WGClientClient` solleva `WGControllerError` per gli errori di comunicazione, nonostante rappresenti un client diretto verso l'API. Conviene correggere questa distinzione prima di ampliare la gestione degli errori.

---

## FASE F — Integrazione del frontend

**Priorità: media-alta.**

Il frontend dovrà coordinare autenticazione, attivazione e gestione dei peer.

### F1. Autenticazione

* [ ] Implementare il flusso di autenticazione con `wg_auth`.
* [ ] Gestire i messaggi del protocollo.
* [ ] Gestire gli errori di autenticazione.
* [ ] Gestire la chiusura della sessione.
* [ ] Evitare di esporre `k_session` a componenti non necessari.
* [ ] Definire dove e per quanto tempo conservare lo stato della sessione nel client.

### F2. Inizializzazione dell'API client

* [ ] Ricevere il risultato dell'attivazione.
* [ ] Ottenere il `listen_path` corretto.
* [ ] Inizializzare il client HTTPS.
* [ ] Configurare l'autenticazione applicativa.
* [ ] Eseguire `GET /v1/status`.
* [ ] Visualizzare l'elenco dei peer restituiti.
* [ ] Gestire gli errori di connessione e le sessioni non più valide.

### F3. Gestione dei peer

* [ ] Implementare l'aggiunta di un peer.
* [ ] Implementare l'aggiornamento di un peer.
* [ ] Implementare la rimozione di un peer.
* [ ] Aggiornare l'interfaccia dopo ogni operazione.
* [ ] Gestire gli errori di validazione.
* [ ] Gestire i conflitti e le modifiche effettuate da altre sessioni.
* [ ] Definire il comportamento dopo la scadenza della sessione.

---

## FASE G — Allineamento del README e delle specifiche

**Priorità: media.**

Il README è già abbastanza dettagliato, ma alcune parti descrivono funzionalità che non risultano ancora implementate oppure non corrispondono esattamente al codice attuale.

* [ ] Allineare il protocollo di attivazione al formato effettivamente inviato da `send_result()`.
* [ ] Documentare che la risposta di attivazione attuale include `protocol_version`, `type`, `status` ed eventualmente `expires_at`, ma non restituisce `session_id` e `listen_path`.
* [ ] Allineare la descrizione dei timestamp in `WGSecureSession` al codice.
* [ ] Documentare il formato definitivo degli header di autenticazione.
* [ ] Aggiornare il diagramma architetturale dopo aver deciso come gestire le istanze HTTPS concorrenti.
* [ ] Documentare il comportamento effettivo degli endpoint HTTP.
* [ ] Aggiornare la sezione relativa alla validazione delle chiavi e degli indirizzi IP.
* [ ] Aggiornare la roadmap con le funzionalità completate e quelle ancora da realizzare.

---


## FASE H — Test, integrazione e hardening finale

**Priorità: alta, prima del deployment.**

### H1. Test unitari

* [ ] Testare `parse_activation()` con pacchetti validi e non validi.
* [ ] Testare `receive_packet()` con pacchetti frammentati, vuoti e troppo grandi.
* [ ] Testare la derivazione delle chiavi di `WGSecureSession`.
* [ ] Testare l'autenticazione di richieste e risposte.
* [ ] Testare il rifiuto dei replay.
* [ ] Testare il parsing degli endpoint HTTP.
* [ ] Testare la validazione dei peer.
* [ ] Testare le eccezioni e i relativi status HTTP.

### H2. Test di integrazione

* [ ] Verificare `wg_auth` → socket IPC → `wg_client`.
* [ ] Verificare che l'ACK venga inviato soltanto dopo il bind HTTPS.
* [ ] Verificare una richiesta autenticata `GET /v1/status`.
* [ ] Verificare l'aggiunta di un peer.
* [ ] Verificare la rimozione di un peer.
* [ ] Verificare una richiesta con MAC errato.
* [ ] Verificare un replay.
* [ ] Verificare una richiesta con sessione scaduta.
* [ ] Verificare l'indisponibilità del controller.
* [ ] Verificare la chiusura ordinata di una sessione.

### H3. Test end-to-end

* [ ] Autenticazione completa dal frontend.
* [ ] Creazione della sessione.
* [ ] Attivazione di `wg_client`.
* [ ] Richiesta dello stato WireGuard.
* [ ] Visualizzazione dei peer nel frontend.
* [ ] Aggiunta e rimozione di peer.
* [ ] Scadenza della sessione.
* [ ] Verifica che una sessione terminata non possa più essere utilizzata.
* [ ] Verifica del comportamento con più client contemporanei.

### H4. Hardening

* [ ] Verificare i permessi sui certificati e sulle chiavi private.
* [ ] Verificare i privilegi effettivi dei servizi systemd.
* [ ] Verificare che `wg_client` non disponga di `CAP_NET_ADMIN`.
* [ ] Verificare che soltanto il controller privilegiato possa modificare WireGuard.
* [ ] Verificare che i segreti non vengano scritti nei log.
* [ ] Definire la gestione delle sessioni dopo un riavvio.
* [ ] Verificare i limiti di risorse per le istanze e i thread.
* [ ] Verificare che un errore di autenticazione non possa provocare operazioni sul controller.

---

# 3. Ordine di implementazione consigliato

Per evitare di dover modificare più volte gli stessi componenti, seguirei questo ordine.

| Ordine | Attività                                              | Risultato atteso                                               |
| ------ | ----------------------------------------------------- | -------------------------------------------------------------- |
| 1      | Stabilizzare `WGSecureSession`                        | Protocollo crittografico definito e testato.                   |
| 2      | Integrare l'autenticazione in `WGClientAPIHandler`    | API HTTPS che verifica effettivamente le richieste.            |
| 3      | Completare `WGClientAPI`                              | Lifecycle, autenticazione e dispatch coordinati.               |
| 4      | Risolvere il problema delle istanze HTTPS concorrenti | Più sessioni gestite secondo il modello architetturale scelto. |
| 5      | Completare `WGClientAPIClient`                        | Client in grado di autenticare richieste e risposte.           |
| 6      | Implementare `wg_auth`                                | Autenticazione e attivazione delle sessioni.                   |
| 7      | Integrare il frontend                                 | Autenticazione e gestione dei peer attraverso l'API.           |
| 8      | Eseguire test end-to-end                              | Verifica dell'intero flusso.                                   |
| 9      | Aggiornare documentazione e hardening                 | Specifiche coerenti con il comportamento effettivo.            |

---

# 4. I tre problemi che affronterei per primi

Se dovessi riprendere il progetto nella tua posizione, partirei da questi tre punti.

### 1. Definire esattamente il protocollo di autenticazione HTTP

Prima di scrivere `wg_auth`, stabilirei definitivamente:

* Quali header vengono inviati.
* Quali campi vengono autenticati.
* Come vengono gestiti i contatori.
* Come vengono autenticate le risposte.
* Come si comportano client e server in presenza di richieste concorrenti.

In questo modo `wg_auth`, `wg_client` e il frontend potranno implementare la stessa specifica senza divergere.

### 2. Completare la pipeline dell'API

Il passaggio successivo sarebbe collegare `WGSecureSession` all'handler e implementare il dispatch.

Questo permetterebbe di verificare l'autenticazione applicativa indipendentemente da OPAQUE e dal frontend.

### 3. Risolvere la gestione delle istanze HTTPS

Questo punto è particolarmente importante per la tua architettura: hai progettato istanze per-sessione, ma il codice attuale tenta di utilizzare lo stesso indirizzo e la stessa porta per ciascuna di esse.

La strategia scelta deve essere definita prima di costruire il servizio di autenticazione, perché determina anche come `wg_auth` comunicherà al client l'indirizzo dell'API.

---

## 5. Checklist sintetica da copiare nella roadmap

Questa è la versione compatta, pronta da riportare in `docs/roadmap.md`.

```markdown
# TODO — wg_manager

## 1. WGSecureSession
- [ ] Definire il formato definitivo dei messaggi autenticati.
- [ ] Allineare il protocollo al codice: timestamp, nonce, counter e MAC.
- [ ] Separare i contatori di invio e ricezione.
- [ ] Gestire la concorrenza e le condizioni di race.
- [ ] Rendere non ambigua la serializzazione dei campi autenticati.
- [ ] Validare rigorosamente nonce, MAC e session ID.
- [ ] Completare l'interfaccia pubblica della sessione.
- [ ] Completare i test crittografici.

## 2. WGClientAPI
- [ ] Integrare WGSecureSession nell'handler HTTP.
- [ ] Implementare authenticate().
- [ ] Implementare dispatch().
- [ ] Autenticare tutte le richieste applicative.
- [ ] Autenticare le risposte.
- [ ] Uniformare la gestione degli errori.
- [ ] Completare la validazione delle richieste HTTP.

## 3. Lifecycle e concorrenza
- [ ] Definire la strategia di bind per sessioni HTTPS concorrenti.
- [ ] Gestire correttamente le istanze per-sessione.
- [ ] Verificare timeout e lettura delle richieste.
- [ ] Gestire lo shutdown con richieste in corso.
- [ ] Verificare la sincronizzazione dello stato delle sessioni.

## 4. WGClientAPIClient
- [ ] Integrare WGSecureSession.
- [ ] Generare e verificare i messaggi autenticati.
- [ ] Separare gli errori API dagli errori del controller.
- [ ] Uniformare la gestione delle eccezioni.
- [ ] Completare i test del client HTTPS.

## 5. WGAuth
- [ ] Definire l'architettura del servizio.
- [ ] Definire il protocollo di autenticazione.
- [ ] Integrare OPAQUE, se confermato come protocollo scelto.
- [ ] Implementare la derivazione di k_session.
- [ ] Implementare il client IPC verso wg_client.
- [ ] Implementare il pacchetto di attivazione.
- [ ] Validare ACTIVATION_RESULT.
- [ ] Gestire errori, timeout e sessioni scadute.
- [ ] Definire persistenza, revoca e lifecycle delle sessioni.

## 6. Frontend
- [ ] Integrare il protocollo di autenticazione.
- [ ] Gestire il risultato dell'attivazione.
- [ ] Inizializzare il client HTTPS.
- [ ] Eseguire GET /v1/status.
- [ ] Visualizzare i peer.
- [ ] Implementare aggiunta, aggiornamento e rimozione dei peer.
- [ ] Gestire errori e scadenza della sessione.

## 7. Test e documentazione
- [ ] Completare i test unitari.
- [ ] Completare i test di integrazione.
- [ ] Completare i test end-to-end.
- [ ] Verificare le sessioni concorrenti.
- [ ] Verificare privilegi, permessi e gestione dei segreti.
- [ ] Allineare README e specifiche al codice effettivo.
- [ ] Aggiornare docs/roadmap.md.
```

**In sintesi:** la tua prossima milestone potrebbe essere *«API HTTPS autenticata end-to-end, indipendentemente dal meccanismo di autenticazione iniziale»*. Una volta raggiunta, avrai un confine applicativo ben definito su cui costruire `wg_auth`, senza dover contemporaneamente modificare il controller privilegiato e il frontend.

# Sistemazione Tests

Sì, secondo me questa è esattamente la fase in cui conviene fermarsi un momento e **riorganizzare la suite di test prima di aggiungere nuove funzionalità**. Dal codice che hai incollato si vede che il progetto `wg-manager` si è evoluto e che i test sono rimasti in parte legati a fasi differenti dello sviluppo.

La cosa importante è che hai già individuato due esigenze distinte:

1. **Non dover eseguire i test come root.** I test devono poter essere lanciati direttamente da PyCharm, nell'ambiente Python del progetto.
2. **Testare il comportamento reale del client**, compreso il ciclo di vita della sessione, senza dover necessariamente avviare systemd, modificare WireGuard o interagire con servizi privilegiati.

Il tuo `test_wg_client_integration.py` è già una buona base per questa impostazione: usa `pytest`, crea configurazioni temporanee, sostituisce il controller con un `FakeController` e simula la socket di attivazione con `socket.socketpair()`.

Non butterei via quel lavoro. Lo userei come riferimento per uniformare gli altri test.

C'è però una distinzione architetturale che terrei ben presente: **simulare systemd non significa dover simulare anche tutto il client**. Possiamo verificare separatamente il protocollo di attivazione, il server HTTPS, il client che comunica con il controller e il comportamento dell'applicazione nel suo complesso.


## 1. Come riorganizzerei `tests/client`

Partirei da una struttura di questo tipo:

```text
tests/
├── conftest.py
│
├── client/
│   ├── conftest.py
│   │
│   ├── unit/
│   │   ├── test_secure_session.py
│   │   ├── test_activation.py
│   │   └── test_client_config.py
│   │
│   ├── api/
│   │   ├── test_api_status.py
│   │   ├── test_api_peers.py
│   │   ├── test_api_errors.py
│   │   └── test_api_lifecycle.py
│   │
│   ├── controller/
│   │   ├── test_controller_client.py
│   │   └── test_controller_errors.py
│   │
│   ├── integration/
│   │   ├── test_client_lifecycle.py
│   │   └── test_controller_integration.py
│   │
│   └── mock/
│       └── test_mock.py
│
└── ...
```

Questa è una proposta di organizzazione, non un'indicazione di creare immediatamente tutti questi file.

L'idea è distinguere i test in base a **quale componente stiamo verificando e da quali dipendenze vogliamo isolarlo**.

| Categoria     | Cosa verifica                                 | Dipendenze                                      |
| ------------- | --------------------------------------------- | ----------------------------------------------- |
| `unit`        | Singole funzioni e classi                     | Dipendenze simulate quando necessario           |
| `api`         | Server HTTPS, routing, validazione e risposte | Controller simulato                             |
| `controller`  | Comunicazione HTTPS con il controller         | Controller reale di test oppure server simulato |
| `integration` | Interazione tra più componenti del client     | Dipendenze simulate dove opportuno              |
| `mock`        | Comportamento del mock WireGuard              | File di stato temporanei                        |

Non è necessario creare subito tutte queste sottocartelle. Possiamo iniziare con tre gruppi e suddividere ulteriormente soltanto quando il numero di test lo giustifica.

### Una precisazione importante

Non trasformerei `test_wg_client_integration.py` in una raccolta di test unitari.

Quel file verifica già diverse interazioni significative tra componenti. Lo manterrei come test di integrazione, spostando fuori da esso le verifiche che possono essere eseguite indipendentemente.

In particolare:

* La validazione del pacchetto di attivazione appartiene ai test unitari.
* Il routing HTTPS e la gestione delle richieste appartengono ai test dell'API.
* Gli errori di comunicazione con il controller appartengono ai test del controller.
* L'attivazione, l'avvio dell'API e il suo arresto possono rimanere nei test di integrazione.

In questo modo evitiamo di verificare continuamente le stesse cose in un unico file enorme.

---

## 2. Il problema di systemd: distinguere il test del protocollo dal test del servizio

Qui secondo me c'è il punto architetturale più interessante.

Attualmente il tuo client riceve un pacchetto di attivazione attraverso una socket Unix. Il test `test_wg_client_integration.py` usa questa funzione:

```python
def run_activation(packet, cfg, monkeypatch):
  """Drive wg_client.activate() over a socketpair like systemd would."""
  monkeypatch.setattr(wg_client, "load_config", lambda: cfg)

  auth, client = socket.socketpair()

  with auth, client:
    auth.sendall(json.dumps(packet).encode() + b"\n")
    result = wg_client.activate(client, lifecycle)
    reply = json.loads(auth.makefile("rb").readline())

  return result, reply
```

È una buona soluzione per testare il protocollo di attivazione senza avviare systemd.

La funzione `socket.socketpair()` crea due estremità di una connessione locale: una può simulare il mittente del pacchetto, mentre l'altra viene passata al codice che normalmente riceverebbe i dati.

Quindi puoi verificare:

1. La ricezione del pacchetto.
2. La sua validazione.
3. La gestione degli errori.
4. La creazione e il bind del server HTTPS.
5. La risposta di conferma dell'attivazione.

Il test non deve avere privilegi root per eseguire queste operazioni.

**Non serve quindi ingannare systemd nel senso di avviare un servizio fittizio completo.** È sufficiente simulare il confine attraverso il quale systemd comunica con il processo, come stai già facendo.

C'è però un miglioramento che prenderei in considerazione.

### Separare la logica di attivazione dal trasporto

Idealmente, il codice dovrebbe distinguere:

* La lettura del pacchetto dalla socket.
* La validazione del pacchetto.
* La creazione della sessione.
* L'avvio del server HTTPS.
* La comunicazione dell'esito al chiamante.

La validazione, in particolare, dovrebbe essere indipendente da systemd e dalle socket.

Nel tuo progetto esiste già:

```python
wg_client_IPC_control_loop.parse_activation(...)
```

Ed è proprio il genere di separazione che vogliamo mantenere.

La funzione di parsing può essere verificata direttamente con test unitari, mentre `activate()` può essere verificata con la socket simulata.

Questo ci permette di coprire due livelli differenti senza duplicare inutilmente il lavoro.


---

## 3. Come distribuirei i test che hai già scritto

Vediamo concretamente dove collocherei il contenuto dei tuoi file.

### A. `test_secure_session.py`

Questo è già un vero test unitario pytest: contiene funzioni `test_...` e non richiede di avviare servizi.

Lo sposterei in:

```text
tests/client/unit/test_secure_session.py
```

Manterrei i test attuali:

* Identità della sessione.
* Generazione di identificativi differenti.
* Autenticazione delle richieste.
* Rilevamento delle alterazioni.
* Rilevamento dei replay.
* Autenticazione delle risposte.

Non vedo motivo di riscriverli soltanto per cambiare la struttura delle cartelle.

### B. `test_client_API.py`

Questo file, invece, è attualmente uno script di avvio manuale.

Contiene un `main()` che avvia il server e attende che l'utente prema Invio.

Non è quindi strutturato come una normale suite pytest.

Lo sposterei nella categoria degli strumenti di test manuali, oppure ne riutilizzerei le parti utili per creare test automatici.

Per esempio, la verifica che il server HTTPS possa essere avviato è già presente nel lifecycle test.

Non avrebbe senso mantenere due test automatici che eseguono esattamente la stessa operazione.

### C. `test_client.py`

Questo file verifica il comportamento del client che comunica con il controller.

I test comprendono:

* Recupero dello stato.
* Aggiunta e rimozione dei peer.
* Rifiuto delle chiavi duplicate.
* Rifiuto degli IP duplicati.
* Validazione delle chiavi e degli IP.
* Gestione degli errori HTTP.

Lo collocherei in:

```text
tests/client/controller/test_controller_client.py
```

Qui c'è però un dettaglio da verificare prima di spostarlo.

Nel codice che hai incollato compare:

```python
from src.wg_client.wg_controller_client import WGClientClient
```

mentre nel lifecycle test utilizzi:

```python
from src.wg_client.wg_controller_client import WGControllerClient
```

Potrebbe essere semplicemente un residuo di una precedente rinominazione, ma **non correggerei questo import alla cieca**: prima verificherei quale sia effettivamente il nome della classe nel modulo attuale.

Anche il percorso dell'API e il metodo HTTP devono essere coerenti con l'implementazione corrente. In particolare, i test di aggiunta dei peer devono verificare la richiesta `PUT` se questa è ormai quella prevista dal protocollo.

### D. `test_wg_client_activator.py`

Questo è un test manuale del protocollo di attivazione attraverso una socket Unix.

Lo terrei disponibile, ma distinguerei il suo ruolo da quello dei test automatici.

Il test automatico può simulare il mittente e verificare il comportamento di `activate()` senza richiedere un servizio systemd realmente attivo.

Lo script manuale, invece, può essere utile per verificare l'interazione con una socket effettivamente predisposta nell'ambiente di test.

Non eliminerei questo strumento: lo sposterei semplicemente fuori dalla suite automatica, se vogliamo evitare che gli script interattivi vengano confusi con i test pytest.

### E. `test_wg_client_integration.py`

Questo diventerebbe:

```text
tests/client/integration/test_client_lifecycle.py
```

Lo manterrei come riferimento principale per i test di integrazione.

La sua struttura è già interessante perché:

* Utilizza `pytest`.
* Simula il controller.
* Crea certificati e configurazioni di test a partire dai file del progetto.
* Utilizza una socket locale per simulare l'attivazione.
* Verifica il bind del server HTTPS.
* Controlla che la sessione non venga avviata quando il bind fallisce.
* Verifica il comportamento del server durante l'arresto.

Sposterei fuori da questo file soltanto i test che hanno una collocazione più naturale in altre categorie.

---

## 4. Un altro miglioramento: condividere le fixture

Attualmente il lifecycle test contiene alcune funzioni che potrebbero essere riutilizzate da altri test:

```python
make_config()
make_packet()
free_port()
```

E contiene anche una fixture:

```python
@pytest.fixture
def api():
    ...
```

Non tutte queste funzioni devono necessariamente essere condivise, ma alcune sono candidate naturali per un `conftest.py`.

Per esempio:

```text
tests/
└── client/
    ├── conftest.py
    ├── unit/
    ├── api/
    ├── controller/
    └── integration/
```

Nel `conftest.py` potremmo mettere le fixture comuni, come:

* Configurazione di test.
* Percorsi dei certificati.
* Pacchetto di attivazione valido.
* Controller simulato.
* Funzioni di supporto per avviare e arrestare il server.

In questo modo ogni test potrà richiedere soltanto le dipendenze che gli servono.

Per esempio, un test dell'API potrebbe ricevere direttamente una fixture `api`, senza dover ricreare manualmente il controller e avviare ogni volta il server.

Naturalmente, le fixture che modificano lo stato dovranno avere uno scope appropriato e occuparsi della pulizia delle risorse.


---

## 5. PyCharm e pytest: rendere l'esecuzione uniforme

Questo è un aspetto che sistemerei subito, perché altrimenti rischiamo di ottenere una suite ben organizzata che però funziona soltanto quando viene lanciata da una particolare directory.

Nel lifecycle test utilizzi:

```python
ROOT = Path(__file__).resolve().parents[2]
```

Questo è ragionevole per individuare la directory principale del progetto dalla posizione del file.

Tuttavia, gli import:

```python
from src.wg_client.wg_client_API import WGClientAPI
```

dipendono anche da come viene configurato il percorso di ricerca dei moduli Python.

Perciò verificherei che PyCharm esegua pytest dalla root del progetto e che `src` sia raggiungibile correttamente.

Possiamo uniformare la configurazione attraverso `pytest.ini` oppure `pyproject.toml`, senza introdurre modifiche artificiali agli import in ogni singolo test.

Un'altra distinzione importante: i tuoi script che hanno soltanto `main()` e un blocco `if __name__ == "__main__":` non diventano automaticamente test pytest.

Per esempio:

```python
def main():
    ...
```

non viene eseguito automaticamente da pytest soltanto perché il file si chiama `test_client.py`.

Quindi dobbiamo decidere esplicitamente quali script convertire in test automatici e quali mantenere come strumenti manuali.

---

# 6. Il piano operativo che ti propongo

Io procederei in questo ordine.

**Fase 1 — Riordino senza modificare la logica**

Creiamo le cartelle e spostiamo i test esistenti nelle rispettive categorie.

In questa fase evitiamo di modificare il comportamento del client o del controller.

**Fase 2 — Uniformazione pytest**

Sistemiamo gli import, la configurazione di PyCharm e le fixture condivise.

L'obiettivo è poter eseguire l'intera suite senza root, senza dover avviare systemd e senza dipendere da un'istanza WireGuard reale.

**Fase 3 — Separazione dei test**

Estraiamo dal lifecycle test le verifiche che possono essere eseguite indipendentemente:

* Parsing e validazione dell'attivazione.
* Gestione delle richieste HTTPS.
* Validazione degli argomenti delle operazioni sui peer.
* Gestione degli errori del controller.
* Comportamento del mock.

**Fase 4 — Conservazione dei test d'integrazione**

Manteniamo un insieme più ristretto di test che verificano l'interazione tra i componenti.

Questi test devono verificare che i componenti funzionino insieme, non ripetere ogni singola verifica già coperta dai test unitari.

**Fase 5 — Verifica della suite completa**

Infine eseguiamo tutti i test da PyCharm e da terminale, controllando che il risultato non dipenda dalla directory corrente o da privilegi particolari.

---

## La mia raccomandazione conclusiva

Non riscriverei tutto da zero.

Hai già una quantità significativa di test utili, e il lifecycle test dimostra che l'approccio pytest con dipendenze simulate funziona.

La cosa che farei è **consolidare l'architettura dei test prima di continuare lo sviluppo del protocollo di pairing**.

In particolare, manterrei separati tre livelli:

1. **Test unitari:** verificano la correttezza delle singole operazioni.
2. **Test d'integrazione:** verificano l'interazione tra client, API e controller.
3. **Test manuali di sistema:** verificano il comportamento nell'ambiente reale, eventualmente con systemd e WireGuard.

In questo modo non dovrai acquisire privilegi per ogni modifica al codice, ma continuerai ad avere la possibilità di verificare il comportamento del programma nell'ambiente di deployment.

**Il prossimo passo concreto**, secondo me, è esaminare i moduli attuali di `src/wg_client`, soprattutto `wg_client.py`, `wg_client_API.py` e `wg_controller_client.py`, insieme alla struttura completa di `tests/`.

Con quelli possiamo stabilire con precisione quali test spostare, quali mantenere invariati e quali correggere per primi, senza rischiare di introdurre regressioni nel codice che hai già funzionante.
