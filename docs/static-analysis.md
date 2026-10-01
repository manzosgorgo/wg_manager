# Static Communication & Protocol Analysis

## 1. Scopo

Questo progetto contiene una pipeline di analisi statica del codice Python finalizzata a ricostruire, senza eseguire il programma, la struttura delle comunicazioni e il flusso dei dati che raggiungono tali comunicazioni.

L'analisi è organizzata in due passaggi distinti:

1. **Communication / Call-Graph Analysis**

   * individua le primitive di comunicazione;
   * identifica le funzioni che le utilizzano;
   * ricostruisce quali chiamanti possono raggiungerle;
   * identifica le possibili radici del percorso.

2. **Protocol / Data-Flow Analysis**

   * utilizza il modello prodotto dal primo passaggio;
   * parte dai communication sink;
   * segue a ritroso le dipendenze dei dati;
   * ricostruisce parametri, costanti, strutture dati, input di rete e trasformazioni;
   * raggruppa i sink in canali e individua elementi condivisi.

In forma concettuale:

```text
                       Python source
                            │
                            ▼
                 ┌─────────────────────┐
                 │ AST / Project model │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       Passo 1       │
                 │  Communication +    │
                 │    Call Graph       │
                 └──────────┬──────────┘
                            │
                communication sinks
                caller relationships
                resolution confidence
                            │
                            ▼
                 ┌─────────────────────┐
                 │       Passo 2       │
                 │   Protocol/Data     │
                 │      Flow           │
                 └──────────┬──────────┘
                            │
                            ▼
                 Protocol representation
```

L'obiettivo non è dimostrare formalmente il comportamento del programma. L'analisi produce invece una **approssimazione strutturale e conservativa** utile per comprendere un progetto reale.

---

## 2. Principi di progettazione

### 2.1 Nessuna esecuzione del codice

L'analizzatore opera sul codice sorgente tramite `ast`.

Non importa né esegue il progetto analizzato.

Questo evita che l'analisi dipenda da:

* stato runtime;
* configurazione locale;
* rete;
* filesystem;
* credenziali;
* side effect;
* codice generato durante l'esecuzione.

Come conseguenza, alcune informazioni che in Python esistono soltanto a runtime non possono essere ricostruite esattamente.

---

### 2.2 Analisi incrementale

Il progetto è deliberatamente diviso in livelli.

Il primo livello risponde principalmente a:

> **Dove avviene comunicazione e attraverso quali percorsi di chiamata ci si arriva?**

Il secondo risponde a:

> **Quali dati possono raggiungere quelle operazioni e da dove provengono?**

Questo evita di costruire immediatamente un gigantesco grafo semantico del progetto.

---

## 3. Passo 1: Communication Analysis

Il primo script identifica le comunicazioni tramite librerie e primitive note.

Attualmente le librerie considerate sono:

* `socket`
* `http.client`
* `http.server`

L'analisi parte dai file che importano direttamente queste librerie nelle forme AST riconosciute.

Da questi file vengono estratte:

* funzioni;
* classi;
* import;
* call site;
* communication primitives;
* chiamate tra funzioni;
* riferimenti a callback;
* informazioni di risoluzione.

Il risultato principale è un modello di:

```text
function → caller → caller → ... → root
```

e contemporaneamente:

```text
function → communication primitive
```

---

## 4. Communication sinks

Un **sink** è una funzione che contiene un'operazione considerata significativa per la comunicazione.

Esempi:

```python
sock.sendall(data)
sock.recv(4096)

conn.request("POST", path, body)
response = conn.getresponse()

server.serve_forever()
server.server_close()
```

Il concetto di sink non coincide necessariamente con una singola istruzione.

Una funzione può contenere più primitive:

```text
foo()
 ├── socket.sendall
 ├── socket.close
 └── ...
```

Per questo l'unità principale del report è la funzione.

---

## 5. Passo 2: Protocol/Data-Flow Analysis

Il secondo script parte dai sink identificati dal primo passaggio e costruisce un grafo di dipendenze.

La direzione dell'analisi è inversa rispetto all'esecuzione:

```text
send(data)
     │
     ▼
    data
     │
     ▼
  variable
     │
     ▼
 parameter
     │
     ▼
 caller argument
     │
     ▼
 constant / input / external value
```

L'analisi cerca quindi le **origini possibili dei dati**.

Questo permette di passare da una descrizione puramente strutturale:

```text
foo → bar → sendall
```

a una descrizione semantica più utile:

```text
foo → bar → sendall
              │
              ├── message shape
              ├── constant
              ├── parameter
              ├── network input
              └── transformation
```

---

## 6. Grafo interno

Il secondo passaggio utilizza diversi tipi di nodo:

| Tipo    | Significato                           |
| ------- | ------------------------------------- |
| `sink`  | funzione contenente una comunicazione |
| `shape` | struttura dati, tipicamente un `dict` |
| `const` | valore letterale                      |
| `ext`   | simbolo esterno/importato             |
| `in`    | input proveniente dalla rete          |
| `open`  | valore che rimane aperto a una root   |
| `param` | parametro formale                     |
| `var`   | variabile                             |
| `attr`  | attributo di oggetto/classe           |
| `xf`    | trasformazione/chiamata intermedia    |

Il grafo non rappresenta necessariamente un control-flow graph.

Rappresenta piuttosto:

> **dipendenze necessarie o possibili per ottenere il valore osservato dal sink.**

---

## 7. Channel model

I sink vengono inoltre raggruppati in base al loro ricevente.

Per esempio:

```text
self.conn.send(...)
self.conn.recv(...)
self.conn.close(...)
```

possono essere ricondotti allo stesso channel.

Nel caso di HTTP server handler viene utilizzata anche l'identità della classe handler.

Questo consente di trasformare una lista di primitive:

```text
send
recv
close
request
response
```

in una rappresentazione più vicina al concetto di:

```text
channel A
 ├── receive
 ├── send
 └── lifecycle

channel B
 ├── request
 └── response
```

---

## 8. Precisione e approssimazione

Python rende impossibile ricostruire sempre un call graph perfetto tramite sola analisi statica.

L'analizzatore usa quindi livelli di confidenza.

Per gli archi del call graph:

```text
exact
import
ref
fuzzy
```

`exact` rappresenta una risoluzione locale diretta.

`import` deriva dalla risoluzione tramite import.

`ref` identifica un riferimento a una funzione passato come oggetto, ad esempio:

```python
register(callback)
```

`fuzzy` è una risoluzione euristica basata sul nome.

I livelli non rappresentano una probabilità statistica. Sono invece una classificazione della tecnica utilizzata per ottenere l'associazione.

---

## 9. Due tipi distinti di confidence

È importante non confondere:

### Call-graph confidence

Descrive come è stato risolto un collegamento:

```text
exact / import / ref / fuzzy
```

### Primitive confidence

Descrive come è stata identificata una primitive:

```text
bound / name-only
```

`bound` significa che il receiver è stato riconosciuto come risorsa di comunicazione.

`name-only` significa invece che il metodo è stato riconosciuto per nome, senza una dimostrazione statica altrettanto forte del receiver.

Queste due classificazioni appartengono a livelli diversi dell'analisi.

---

## 10. Output

La pipeline può produrre due tipi di output:

### Report umano

Pensato per l'ispezione manuale.

### JSON

Pensato come rappresentazione intermedia per tool successivi.

Il JSON non dovrebbe essere considerato automaticamente una API pubblica stabile, a meno che non venga esplicitamente versionato.

Un possibile utilizzo futuro è:

```text
AST
 │
 ▼
analysis
 │
 ├── callgraph.json
 │
 └── protocol.json
       │
       ├── architecture generator
       ├── protocol verifier
       ├── documentation generator
       └── visualization
```

---

## 11. Limiti generali

L'analisi non tenta di risolvere completamente le caratteristiche dinamiche di Python.

In particolare possono essere problematici:

* `getattr`;
* reflection;
* monkey patching;
* decorator complessi;
* dispatch dinamico;
* callable conservati in dizionari;
* codice generato;
* import dinamici;
* metaprogrammazione;
* aliasing complesso;
* effetti collaterali non rappresentati dall'AST;
* informazioni disponibili esclusivamente a runtime.

Il risultato deve quindi essere interpretato come una **static approximation**.

---

## 12. Filosofia del progetto

La pipeline non tenta di sostituire il codice sorgente.

Il suo scopo è produrre una rappresentazione intermedia sufficientemente ricca da permettere a strumenti successivi di ragionare sul progetto.

Il modello risultante può essere visto come una progressiva riduzione:

```text
source code
    │
    ▼
structural model
    │
    ▼
communication model
    │
    ▼
data-flow model
    │
    ▼
protocol model
```

Il vantaggio di questa separazione è che ogni livello può essere analizzato, validato o visualizzato indipendentemente dagli altri.
