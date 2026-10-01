# `protocol_flow.py`

## Backward Protocol Data-Flow Analysis

## 1. Scopo

`protocol_flow.py` è il secondo passaggio della pipeline di analisi statica.

Il suo obiettivo è rispondere alla domanda:

> **Quali dati possono raggiungere le operazioni di comunicazione e da quali sorgenti provengono?**

Lo script non cerca semplicemente le chiamate di rete.

Parte dai communication sinks individuati dal primo passaggio e costruisce un **backward dependency graph**.

La direzione concettuale è:

```text
                         runtime
                            │
                            ▼
                    communication sink
                            │
                            ▼
                         value
                            │
                            ▼
                       dependency
                            │
                            ▼
                     source / leaf
```

L'analisi viene eseguita in senso inverso:

```text
send(message)
     │
     ▼
  message
     │
     ▼
 parameter
     │
     ▼
 caller argument
     │
     ▼
 constant / input / external symbol
```

---

# 2. Dipendenza dal Passo 1

Il modulo importa:

```python
import sink_callergraph as cg
```

e riutilizza il progetto/call graph costruito dal primo analizzatore.

Non ricostruisce quindi da zero la struttura delle chiamate.

Questo è importante perché il secondo passaggio può concentrarsi sul problema più specifico della dipendenza dei dati.

---

# 3. Input logico

Il punto di partenza è ogni funzione che contiene una primitive di comunicazione.

Per ogni primitive vengono considerate:

* gli argomenti posizionali;
* gli argomenti keyword;
* il receiver, quando significativo.

Per esempio:

```python
sock.sendall(payload)
```

produce concettualmente:

```text
sink
 │
 ├── receiver: sock
 └── payload
```

mentre:

```python
conn.request("POST", path, body)
```

produce:

```text
sink
 │
 ├── conn
 ├── "POST"
 ├── path
 └── body
```

---

# 4. Backward slicing

La funzione centrale dell'analisi è `slice()`.

Dato un'espressione:

```python
x
```

l'analizzatore cerca come `x` è stato definito.

Esempio:

```python
payload = build_payload()
sock.sendall(payload)
```

viene trasformato concettualmente in:

```text
sendall
  │
  ▼
payload
  │
  ▼
build_payload()
```

Se `build_payload()` è una funzione del progetto, l'analisi può entrare nella funzione e continuare a seguire il valore.

---

# 5. Tipi di nodo

Il grafo utilizza diversi tipi di nodo.

## `sink`

Una funzione che contiene una communication primitive.

Esempio:

```text
sink:foo
```

---

## `shape`

Una struttura dati, normalmente un `dict`.

Esempio:

```python
{
    "action": "add",
    "peer": key,
}
```

può diventare una shape con campi:

```text
action
peer
```

---

## `const`

Un valore letterale.

Esempi:

```python
"add"
42
True
None
```

---

## `ext`

Un simbolo esterno o importato.

Per esempio:

```python
os.environ
SomeImportedConstant
```

quando non è possibile ridurlo ulteriormente a un valore locale.

---

## `in`

Input proveniente dalla rete.

Esempi:

```python
sock.recv(...)
request.rfile.read(...)
response.read(...)
```

---

## `open`

Un valore che non può essere ulteriormente risolto perché rimane aperto a una root.

Rappresenta un punto nel quale il comportamento dipende da un input esterno al modello analizzato.

---

## `param`

Parametro formale di una funzione.

Esempio:

```python
def send_message(payload):
    ...
```

---

## `var`

Variabile locale o di modulo.

---

## `attr`

Attributo di oggetto o classe.

In particolare:

```python
self.token
self.conn
```

---

## `xf`

Trasformazione o funzione intermedia.

Rappresenta una chiamata della quale il grafo non ha potuto o non ha scelto di ricostruire completamente il risultato.

---

# 6. Expression analysis

Lo slicing gestisce diversi tipi di espressione.

## Costanti

```python
"hello"
```

diventa un nodo `const`.

---

## Nomi

```python
payload
```

viene risolto cercando:

1. parametro;
2. variabile;
3. funzione/enclosing scope;
4. variabile di modulo;
5. simbolo importato.

---

## Attributi

Per:

```python
self.payload
```

vengono cercate le definizioni dell'attributo nella classe.

La ricerca può attraversare anche le classi base.

---

## Subscript

Per:

```python
payload["token"]
```

il grafo considera sia:

```text
payload
```

sia:

```text
"token"
```

come dipendenze.

Questa scelta evita di perdere la relazione fra contenitore e indice.

---

# 7. Message shapes

Uno degli elementi più importanti del secondo passaggio è il riconoscimento dei dizionari.

Esempio:

```python
message = {
    "command": "add",
    "public_key": key,
    "endpoint": endpoint,
}
```

viene rappresentato come una `shape`.

Concettualmente:

```text
shape
 ├── command ──► "add"
 ├── public_key ──► key
 └── endpoint ──► endpoint
```

Questo permette al report di descrivere non solo che un oggetto raggiunge un sink, ma anche la sua struttura.

---

# 8. Dict mutation

Sono considerate anche alcune modifiche successive ai dizionari.

Per esempio:

```python
message = {
    "command": "add"
}

message["key"] = key
```

può essere ricostruito come una singola shape concettuale:

```text
message
 ├── command
 └── key
```

Sono inoltre considerate alcune forme di:

```python
message.update(...)
```

Quando non esiste una shape precedente viene generata una shape mutabile separata.

---

# 9. Parameters

I parametri sono uno dei punti nei quali il grafo deve attraversare un confine di funzione.

Esempio:

```python
def send_message(payload):
    sock.sendall(payload)

def handler():
    send_message(message)
```

Lo slicing deve stabilire:

```text
payload
   ▲
   │
message
```

Per questo vengono utilizzati i call site costruiti dal primo passaggio.

---

# 10. Upward mode

Quando un parametro viene analizzato in modalità upward:

```text
callee parameter
       ▲
       │
caller argument
       ▲
       │
caller
```

l'analizzatore cerca tutti i call site della funzione.

Se non trova un caller noto, viene generato un nodo:

```text
open
```

Questo significa che il valore è lasciato aperto rispetto al modello corrente.

---

# 11. Downward mode

Durante la discesa in una funzione chiamata, il comportamento è differente.

Dato:

```python
send_message(message)
```

e:

```python
def send_message(payload):
    ...
```

il parametro viene legato direttamente a:

```text
payload ← message
```

Questo evita di mescolare i valori provenienti da call site differenti.

---

# 12. Perché esistono due modalità

Senza questa distinzione sarebbe facile introdurre contaminazioni.

Per esempio:

```python
send(a)
send(b)
```

non dovrebbe produrre automaticamente:

```text
a ↔ b
```

La modalità downward mantiene il contesto della singola chiamata.

La modalità upward invece permette di risalire dai parametri alle possibili origini.

---

# 13. Call descent

Quando una chiamata appartiene a una funzione del progetto, il risultato della chiamata può essere seguito attraverso i `return`.

Esempio:

```python
def make_message(key):
    return {
        "key": key
    }

payload = make_message(peer)
send(payload)
```

il grafo può seguire:

```text
send
 │
 ▼
payload
 │
 ▼
make_message(...)
 │
 ▼
shape
 └── key
```

---

# 14. `--max-ctx`

La discesa attraverso le funzioni è limitata da:

```text
--max-ctx
```

Il valore predefinito è:

```text
3
```

Questo limita la profondità del contesto utilizzato per seguire le chiamate.

È una misura sia di complessità sia di controllo sull'over-approximation.

---

# 15. Fuzzy descent

Per default la discesa nei return privilegia risoluzioni:

```text
exact
import
```

La discesa fuzzy può essere abilitata con:

```text
--descend-fuzzy
```

Questo aumenta il recall ma può introdurre associazioni ambigue.

---

# 16. Network inputs

Alcune primitive sono trattate come sorgenti di input esterno.

L'insieme comprende:

```text
recv
recv_into
recvfrom
recvmsg
read
read1
readline
readinto
getresponse
getheader
getheaders
rfile.read
rfile.readline
```

Quando una di queste primitive viene raggiunta durante lo slicing, viene generato un nodo:

```text
in:<library>.<primitive>
```

Questo permette di distinguere:

```text
constant
```

da:

```text
network input
```

---

# 17. Transformations

Non tutte le chiamate devono essere espanse.

Una chiamata può essere rappresentata come:

```text
xf:<label>
```

quando costituisce una trasformazione intermedia.

Esempio:

```python
encoded = encode(payload)
send(encoded)
```

può essere rappresentato come:

```text
send
 │
 ▼
xf:encode
 │
 ▼
payload
```

Le funzioni considerate rumore vengono filtrate tramite `XF_NOISE`.

Tra queste:

```text
len
isinstance
list
dict
tuple
set
sorted
range
min
max
sum
abs
print
enumerate
zip
repr
str
bool
float
int
getattr
hasattr
type
super
```

---

# 18. Facts

La classe `Facts` raccoglie le informazioni locali necessarie allo slicing.

Tra le informazioni memorizzate:

* parametri;
* default;
* varargs;
* kwargs;
* definizioni di variabili;
* definizioni di attributi `self`;
* return;
* assegnamenti;
* mutazioni di dizionari.

L'estrazione viene effettuata tramite una visita AST controllata.

---

# 19. Assegnamenti

Gli assegnamenti vengono trasformati in fatti.

Esempio:

```python
x = value
```

diventa concettualmente:

```text
x ← value
```

Per destructuring:

```python
a, b = pair
```

il modello mantiene le relazioni tra gli elementi.

Sono inoltre trattati:

* tuple/list destructuring;
* starred assignment;
* `with`;
* loop bindings;
* walrus operator;
* return;
* aggiornamenti di dizionari.

---

# 20. Funzioni annidate

La raccolta dei facts è intenzionalmente **shallow**.

Durante l'analisi di una funzione non vengono attraversati automaticamente:

* funzioni annidate;
* classi annidate;
* lambda.

Questo evita che definizioni appartenenti a scope differenti vengano accidentalmente fuse nel modello della funzione corrente.

---

# 21. `self` e classi

Gli attributi di:

```python
self.x
```

possono essere definiti in punti differenti della classe.

Il resolver cerca le definizioni della classe e delle classi base.

Questo permette di seguire pattern come:

```python
class A:
    def __init__(self):
        self.conn = make_connection()

class B(A):
    def send(self, data):
        self.conn.sendall(data)
```

---

# 22. Sink analysis

I sink vengono raggruppati per funzione.

Per ogni funzione viene creato un nodo:

```text
sink:<function>
```

Ogni primitive viene quindi analizzata.

Per una call:

```python
obj.send(data)
```

vengono considerate:

```text
data
obj
```

Per una funzione:

```python
send(data, key=key)
```

vengono considerate entrambe le dipendenze.

---

# 23. Receiver/channel

Il receiver è importante perché identifica il canale sul quale avviene la comunicazione.

Per esempio:

```python
self.conn.send(...)
self.conn.close()
```

condivide il receiver:

```text
self.conn
```

I sink vengono quindi raggruppati per channel.

Questo consente al report di produrre una sezione come:

```text
## Canali
```

invece di una semplice lista piatta di primitive.

---

# 24. Handler channels

Per gli HTTP handler viene applicato un trattamento speciale.

Più primitive appartenenti allo stesso handler possono essere raggruppate tramite la classe handler anche quando il receiver non è rappresentabile esattamente come un normale attributo.

---

# 25. Cone

Per ogni sink viene costruito il relativo **dependency cone**.

Il cone rappresenta l'insieme dei nodi dai quali il sink dipende secondo il modello statico.

La traversal può fermarsi su determinati nodi terminali, come le shape, oppure attraversarli ulteriormente quando richiesto internamente.

---

# 26. Constants

`reach_consts()` raccoglie le costanti raggiungibili dal sink.

Questo è utile per individuare valori come:

```text
"status"
"add"
"delete"
"/v1/peers"
42
True
```

Non significa però che questi siano necessariamente i soli valori runtime possibili.

Rappresentano i literal raggiungibili nel modello statico.

---

# 27. Parameter values

Il report cerca anche parametri che possono assumere più valori costanti.

Questo consente di ottenere informazioni del tipo:

```text
parameter X
 ├── "status"
 ├── "add"
 └── "delete"
```

La presenza di più valori rende il parametro particolarmente interessante dal punto di vista del protocollo.

---

# 28. Intersections

Uno degli output più utili è l'analisi delle intersezioni.

Se due sink dipendono dalla stessa struttura o dallo stesso nodo:

```text
sink A ──► node X
sink B ──► node X
```

`X` rappresenta una possibile relazione condivisa.

Le intersezioni possono riguardare:

* nodi nominali;
* shape;
* costanti;
* altre leaf values.

Questo permette di trovare elementi comuni tra parti apparentemente separate del protocollo.

---

# 29. Report

Il report principale contiene:

```text
# Snapshot del protocollo (passo 2)
```

seguito da:

1. statistiche;
2. canali;
3. forme dei messaggi;
4. valori costanti dei parametri;
5. dettaglio dei sink;
6. intersezioni.

---

# 30. Canali

La sezione:

```text
## Canali
```

raggruppa i sink che condividono un receiver.

Il risultato descrive quindi l'organizzazione delle comunicazioni per canale.

---

# 31. Forme dei messaggi

La sezione:

```text
## Forme dei messaggi
```

riporta le shape individuate.

Per esempio, un messaggio può essere sintetizzato come:

```text
{
    command: const("add")
    peer: param(...)
    endpoint: var(...)
}
```

La forma è una descrizione statica delle dipendenze, non necessariamente uno schema runtime completo.

---

# 32. Sink details

Per ogni sink vengono riportati, quando presenti:

* posizione delle primitive;
* trasformazioni;
* costanti;
* simboli esterni;
* input di rete;
* input root aperti;
* numero di shape.

Questo permette di passare dal quadro generale al singolo punto di comunicazione.

---

# 33. Intersections

La sezione:

```text
## Intersezioni
```

mostra elementi condivisi tra più sink.

Questa parte è particolarmente utile per riconoscere:

* protocolli con campi comuni;
* identificatori condivisi;
* costanti di stato;
* strutture riutilizzate;
* parametri che influenzano più operazioni.

---

# 34. JSON

Il JSON contiene principalmente:

```text
nodes
edges
fields
sinks
channel
```

Questa struttura rappresenta il grafo costruito dall'analisi.

È particolarmente adatta come input per tool futuri:

```text
visualizer
protocol verifier
schema generator
documentation generator
architecture extractor
```

---

# 35. CLI

Uso generale:

```bash
python protocol_flow.py [repo]
```

Opzioni:

```text
--json OUT
--only SUBSTRING
--kinds KINDS
--strict
--no-tests
--exclude NAME
--max-ctx N
--descend-fuzzy
--no-fuzzy-sites
--max-fuzzy N
--max-nodes N
--limit N
```

---

# 36. `--kinds`

Il default comprende:

```text
io,lifecycle,setup
```

Il Passo 2 include quindi anche le primitive di setup, a differenza del default del Passo 1.

Questo permette di analizzare eventi come:

```text
connect
bind
listen
serve_forever
```

quando sono rilevanti per il modello.

---

# 37. `--strict`

Come nel Passo 1, limita i sink alle primitive con:

```text
confidence = bound
```

e quindi esclude le primitive `name-only`.

---

# 38. `--only`

Permette di restringere l'analisi ai sink il cui function identifier contiene la stringa specificata.

Non è un filtro semantico sul protocollo: è un filtro testuale sul riferimento alla funzione.

---

# 39. `--max-ctx`

Controlla la profondità massima del contesto utilizzato durante la discesa attraverso le chiamate.

Default:

```text
3
```

Un valore più alto permette di ricostruire catene più profonde ma aumenta costo e possibilità di over-approximation.

---

# 40. `--descend-fuzzy`

Abilita la discesa nei return anche attraverso risoluzioni fuzzy.

È utile per esplorazioni più aggressive, ma può introdurre dipendenze ambigue.

---

# 41. `--no-fuzzy-sites`

Disabilita l'uso dei fuzzy call site durante la propagazione upward dei parametri.

È quindi distinto da:

```text
--descend-fuzzy
```

che controlla invece la discesa nei return.

---

# 42. `--max-fuzzy`

Limita l'esplosione combinatoria delle associazioni fuzzy.

---

# 43. `--max-nodes`

Imposta il numero massimo di nodi prodotti dall'analisi.

Default:

```text
50000
```

Se il limite viene raggiunto, l'analisi viene marcata come troncata.

Un report troncato non deve essere interpretato come completo.

---

# 44. `--limit`

Controlla il numero di elementi mostrati nelle sezioni sintetiche del report.

È principalmente un controllo di leggibilità dell'output, distinto da `--max-nodes`, che controlla l'analisi.

---

# 45. Noise model

Il modello include un insieme di funzioni considerate generalmente non informative per il protocollo.

Per esempio:

```python
len(x)
str(x)
int(x)
repr(x)
```

non vengono normalmente trattate come sorgenti semantiche indipendenti.

Queste operazioni possono essere rappresentate come trasformazioni filtrate o ignorate a seconda del contesto.

---

# 46. Limitazioni del data-flow

## Path sensitivity

Il modello non è completamente path-sensitive.

Per esempio:

```python
if condition:
    x = "A"
else:
    x = "B"
```

può essere rappresentato come un insieme di possibili definizioni.

Non viene necessariamente dimostrata la correlazione:

```text
condition == true  → x == "A"
condition == false → x == "B"
```

---

## Aliasing

Aliasing complesso tra oggetti e contenitori non viene risolto completamente.

---

## Mutation

La mutation è riconosciuta solo per un insieme definito di pattern:

* assegnamento;
* subscript assignment;
* `dict.update`;
* alcuni binding strutturali.

---

## Instance identity

Gli attributi `self.x` possono essere sovra-approssimati quando più istanze della stessa classe condividono la stessa struttura statica.

---

## Dynamic Python

Restano difficili:

```text
reflection
dynamic dispatch
getattr
dynamic imports
generated code
monkey patching
runtime registration
```

---

# 47. Network input ≠ arbitrary external input

Il nodo:

```text
in
```

rappresenta specificamente un input riconosciuto come proveniente dalle primitive di comunicazione note.

Non significa che l'analizzatore abbia dimostrato che il valore provenga necessariamente da un attaccante o da una rete non fidata.

Rappresenta soltanto:

> valore derivato da una sorgente di input di rete riconosciuta dal modello.

---

# 48. Open input

Il nodo:

```text
open
```

ha un significato differente.

Indica un valore che resta non risolto rispetto alle root del modello.

Per esempio:

```python
def handle(payload):
    send(payload)
```

se `handle` non ha caller noto può produrre:

```text
open → payload
```

Questo è un modo per conservare informazione senza inventare una sorgente.

---

# 49. Static protocol snapshot

Il report prodotto da questo script può essere interpretato come uno:

> **snapshot statico del protocollo osservabile nel codice.**

Non è necessariamente uno schema formale del protocollo.

In particolare:

```text
shape
```

non equivale automaticamente a:

```text
JSON schema
```

e:

```text
const
```

non equivale automaticamente a:

```text
enumeration completa dei valori runtime
```

---

# 50. Relazione con il primo passaggio

La divisione delle responsabilità è:

```text
comm_callgraph.py
    │
    ├── "dove?"
    ├── "chi?"
    └── "attraverso quale percorso?"
             │
             ▼
protocol_flow.py
    │
    ├── "cosa?"
    ├── "da dove?"
    ├── "con quale forma?"
    └── "cosa condividono i sink?"
```

Il primo costruisce il **modello di comunicazione**.

Il secondo costruisce il **modello delle dipendenze del protocollo**.

---

# 51. Esempio completo

Consideriamo:

```python
def make_request(key):
    return {
        "action": "add",
        "key": key,
    }

def send_request(conn, key):
    payload = make_request(key)
    conn.sendall(payload)
```

Il primo passaggio individua:

```text
send_request
    │
    └── socket.sendall
```

e il caller graph può produrre:

```text
handle
  └── send_request
       └── socket.sendall
```

Il secondo passaggio può invece produrre:

```text
sink:send_request
    │
    ▼
shape
 ├── action ──► const("add")
 └── key ─────► param(key)
```

Se `key` viene passato da una funzione superiore:

```text
sink
 │
 ▼
shape
 │
 └── key
       │
       ▼
     caller
       │
       ▼
    parameter
       │
       ▼
     open/input/constant
```

Il risultato è quindi una rappresentazione del protocollo molto più ricca della semplice presenza di `sendall`.

---

# 52. Complessità

Il parametro più importante dal punto di vista della complessità è il numero di possibili percorsi.

I principali meccanismi di contenimento sono:

```text
--max-fuzzy
--max-ctx
--max-nodes
```

oltre a:

* memoization;
* recursion guards;
* eliminazione del noise;
* esclusione di directory;
* limitazione della profondità dei caller tree.

La presenza di un limite raggiunto non deve essere nascosta: il report mantiene una condizione di truncation.

---

# 53. Utilizzo consigliato

Analisi esplorativa:

```bash
python protocol_flow.py . \
    --kinds io,lifecycle,setup \
    --json protocol.json
```

Analisi conservativa:

```bash
python protocol_flow.py . \
    --strict \
    --no-fuzzy-sites \
    --json protocol.json
```

Analisi mirata:

```bash
python protocol_flow.py . \
    --only WGAuthAPIHandler \
    --json auth-protocol.json
```

Analisi più aggressiva:

```bash
python protocol_flow.py . \
    --descend-fuzzy \
    --max-ctx 5 \
    --max-fuzzy 20
```

---

# 54. Uso futuro come IR

Il grafo prodotto da questo script può costituire una base per strumenti ulteriori.

Per esempio:

```text
protocol.json
      │
      ├── Graph visualization
      │
      ├── Protocol documentation
      │
      ├── Message schema extraction
      │
      ├── Static consistency checks
      │
      ├── Client/server matching
      │
      └── Protocol regression detection
```

Questo è uno dei motivi per cui la rappresentazione interna è mantenuta separata dal report testuale.

---

# 55. Interpretazione finale

`protocol_flow.py` non tenta di dire:

> "questo è esattamente il protocollo runtime".

Produce invece:

> "queste sono le dipendenze dei dati e le strutture del protocollo che possono essere ricostruite staticamente dal codice analizzato."

La distinzione è fondamentale.

Il valore principale dello strumento è trasformare codice Python dinamico e distribuito in una rappresentazione esplicita:

```text
communication
      │
      ▼
     sink
      │
      ▼
    shape
      │
      ├── constants
      ├── parameters
      ├── attributes
      ├── external symbols
      ├── network input
      └── transformations
```

Questa rappresentazione costituisce il secondo livello dell'IR della pipeline e può essere utilizzata da strumenti successivi senza dover nuovamente analizzare il sorgente.
