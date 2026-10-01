# `comm_callgraph.py`

## Communication Sink Discovery and Caller Analysis

## 1. Scopo

`comm_callgraph.py` è il primo passaggio della pipeline di analisi statica.

Il suo compito è individuare:

1. i file che utilizzano primitive di comunicazione note;
2. le funzioni che contengono tali primitive;
3. le chiamate tra le funzioni del progetto;
4. i percorsi di chiamata che raggiungono una funzione di comunicazione;
5. le possibili root dalle quali tali funzioni possono essere raggiunte.

L'analisi è completamente statica e basata sull'AST Python.

Il codice analizzato **non viene eseguito**.

---

# 2. Modello concettuale

Il programma costruisce due relazioni principali.

### Communication relation

```text
function ──────► communication primitive
```

### Caller relation

```text
caller ──────► callee
```

Da queste relazioni è possibile risalire:

```text
communication sink
        ▲
        │
      caller
        ▲
        │
      caller
        ▲
        │
       root
```

Il report combina quindi **sink discovery** e **caller reachability**.

---

# 3. Librerie analizzate

Le librerie riconosciute sono:

```python
socket
http.client
http.server
```

L'analizzatore cerca import diretti nelle forme AST supportate, per esempio:

```python
import socket
import http.client
from socket import socket
from http.client import HTTPSConnection
```

La presenza di un import è importante perché limita il dominio nel quale vengono applicate alcune euristiche.

Non viene eseguita una ricerca dinamica delle librerie importate a runtime.

---

# 4. Communication primitives

## 4.1 `socket`

### Creazione

Sono riconosciuti:

```python
socket.socket(...)
socket.create_connection(...)
socket.create_server(...)
socket.fromfd(...)
```

e:

```python
socket.socketpair(...)
```

per la creazione di più risorse.

### Setup

```text
connect
connect_ex
bind
listen
accept
```

### I/O

```text
send
sendall
sendto
sendmsg
sendfile
recv
recv_into
recvfrom
recvmsg
makefile
```

### Lifecycle

```text
close
shutdown
detach
```

---

# 5. `http.client`

Sono riconosciuti i principali oggetti:

```python
HTTPConnection
HTTPSConnection
```

### I/O

```text
request
putrequest
putheader
endheaders
send
getresponse
read
read1
readinto
getheader
getheaders
```

### Setup

```text
connect
```

### Lifecycle

```text
close
```

---

# 6. `http.server`

Per gli oggetti server sono riconosciuti:

```python
HTTPServer
ThreadingHTTPServer
```

### Lifecycle/setup

```text
serve_forever
handle_request
shutdown
server_close
```

---

# 7. HTTP handlers

Lo script contiene una gestione specifica dei pattern tipici di `BaseHTTPRequestHandler`.

Per una classe riconosciuta come handler possono essere considerate primitive anche operazioni come:

```python
self.wfile.write(...)
self.rfile.read(...)
self.rfile.readline(...)
self.send_response(...)
self.send_response_only(...)
self.send_header(...)
self.end_headers(...)
self.send_error(...)
```

e l'accesso a:

```text
self.headers
self.path
self.command
self.close_connection
```

Questo permette di riconoscere la comunicazione anche quando non appare esplicitamente come:

```python
socket.send(...)
```

---

# 8. Binding delle risorse

Uno dei problemi principali dell'analisi è stabilire se:

```python
x.send(data)
```

sia realmente una comunicazione.

Lo script tenta quindi di ricostruire quali variabili contengano risorse di comunicazione.

Esempio:

```python
sock = socket.socket()
...
sock.sendall(data)
```

produce concettualmente:

```text
sock → socket
```

e successivamente:

```text
sock.sendall → socket / io
```

---

## 8.1 Fixed point

Il binding viene propagato iterativamente fino a un massimo di sei passaggi.

Questo permette di gestire catene come:

```python
a = socket.socket()
b = a
c = b
d = c
d.sendall(data)
```

senza richiedere che la relazione sia direttamente visibile nella stessa istruzione.

Il limite di sei iterazioni impedisce che un progetto patologico trasformi questa fase in un'analisi senza terminazione pratica.

---

# 9. Propagazione speciale

Alcune API producono o trasformano risorse.

L'analizzatore tratta esplicitamente casi come:

```python
conn, addr = sock.accept()
```

dove il primo elemento del risultato è considerato una socket.

Sono inoltre seguite alcune propagazioni tramite:

```text
makefile
dup
getresponse
```

quando possono mantenere una relazione con la risorsa comunicativa.

---

# 10. Name-only detection

Quando il receiver non può essere associato staticamente a una risorsa nota, lo script dispone di una seconda euristica.

Esempio:

```python
obj.sendall(data)
```

Se `obj` non può essere identificato, il metodo può comunque essere considerato sospetto in un file che importa una libreria di comunicazione.

Questa modalità produce:

```text
confidence = name-only
```

anziché:

```text
confidence = bound
```

La modalità `name-only` aumenta il recall ma può produrre falsi positivi.

---

# 11. Funzioni e classi

Ogni funzione viene rappresentata internamente tramite `FuncInfo`.

Le informazioni principali comprendono:

```text
id
relative path
qualified name
name
class
line
AST node
```

Per le classi viene utilizzato `ClassInfo`, contenente:

```text
relative path
name
bases
methods
```

Le funzioni di modulo sono rappresentate normalmente.

Quando è necessario rappresentare codice eseguito a livello modulo viene utilizzato un nodo pseudo-funzione:

```text
<module>
```

---

# 12. Call sites

Durante la visita AST vengono raccolti tutti i call site.

Per esempio:

```python
foo()
obj.bar(x)
module.func(y)
```

diventano candidati per la costruzione del call graph.

La risoluzione avviene in più livelli.

---

# 13. Call resolution

L'ordine concettuale è:

```text
1. local exact
2. imported symbol/module
3. reference
4. fuzzy name/method
```

## Exact

Una chiamata può essere associata direttamente a una funzione locale o a un metodo noto.

## Import

La risoluzione può attraversare gli import.

## Reference

Una funzione passata come oggetto può essere identificata come callback.

Esempio:

```python
register(callback)
```

## Fuzzy

Quando non è possibile una risoluzione più precisa, viene utilizzato il nome della funzione/metodo.

Questa è l'ultima risorsa perché può associare più candidati.

---

# 14. Confidence ranking

Gli archi vengono ordinati per qualità:

```text
exact  = 0
import = 1
ref    = 2
fuzzy  = 3
```

Se esistono più associazioni per lo stesso collegamento, viene mantenuta quella con ranking migliore.

Questo non significa che `fuzzy` sia necessariamente falso: significa semplicemente che l'evidenza statica è più debole.

---

# 15. Fuzzy matching

Il numero di candidati fuzzy viene limitato tramite:

```text
--max-fuzzy
```

Questo è importante nei progetti grandi.

Senza un limite, un metodo comune come:

```python
close()
```

potrebbe essere associato a moltissime funzioni apparentemente compatibili.

Sono inoltre filtrati alcuni nomi generici tramite `COMMON_NOISE`.

---

# 16. Callback references

Lo script riconosce riferimenti a funzioni passati come argomenti:

```python
register(handler)
```

oppure:

```python
start(callback=handler)
```

Questi archi vengono marcati:

```text
ref
```

e sono trattati diversamente dalle normali call expression.

---

# 17. Caller graph

Una volta risolti i call site viene costruito il grafo dei chiamanti.

Concettualmente:

```text
A → B → C
```

significa:

```text
A può chiamare B
B può chiamare C
```

Per un sink `C`, l'analizzatore può quindi risalire:

```text
C
↑
B
↑
A
```

---

# 18. Root

Una root è una funzione che, nel call graph ricostruito, non possiede chiamanti conosciuti.

Questo **non significa necessariamente** che sia un entry point applicativo formale.

Può essere:

* una vera entry point;
* una funzione invocata dinamicamente;
* un handler registrato esternamente;
* una funzione il cui caller non è stato risolto;
* codice a livello modulo.

Per questo il termine `root` deve essere interpretato come:

> nodo senza caller conosciuto nel modello statico corrente.

---

# 19. `reachable_roots`

Per ogni sink, `reachable_roots()` risale ricorsivamente gli archi dei chiamanti.

Il risultato è l'insieme delle root dalle quali il sink è raggiungibile nel grafo.

La ricerca non filtra automaticamente gli archi fuzzy.

Di conseguenza, un risultato può dipendere anche da una risoluzione euristica.

---

# 20. Caller tree

`caller_tree()` produce una rappresentazione testuale dell'albero dei chiamanti.

Esempio concettuale:

```text
socket.sendall
├── send_message
│   └── handle_request
│       └── run
└── reply
    └── handle_connection
```

Il tree è pensato per l'ispezione umana.

Non deve essere interpretato come una enumerazione matematica completa di tutti i cammini.

Vengono infatti gestiti:

* cicli;
* espansioni duplicate;
* profondità massima.

---

# 21. CLI

Uso generale:

```bash
python comm_callgraph.py [repo]
```

Opzioni principali:

```text
--json OUT
--strict
--kinds KINDS
--no-tests
--max-depth N
--max-fuzzy N
--exclude NAME
```

---

## `--kinds`

Controlla quali categorie di primitive considerare.

Valore predefinito:

```text
io,lifecycle
```

È possibile includere anche:

```text
setup
```

---

## `--strict`

Mantiene solamente primitive con:

```text
confidence = bound
```

e quindi elimina la classificazione `name-only`.

È utile quando si vuole privilegiare precisione rispetto a recall.

---

## `--no-tests`

Esclude i test dall'analisi.

---

## `--max-depth`

Limita la profondità del caller tree.

Non modifica necessariamente l'intero call graph interno.

---

## `--max-fuzzy`

Limita il numero di candidati associabili tramite fuzzy resolution.

---

## `--exclude`

Aggiunge directory o nomi all'elenco delle esclusioni.

---

# 22. Esclusioni predefinite

Tra le directory escluse:

```text
.git
.idea
.venv
venv
__pycache__
.pytest_cache
node_modules
dist
build
coverage
site-packages
login
tests
```

L'elenco è pensato per eliminare codice generalmente irrilevante per l'architettura applicativa.

---

# 23. Output

Il report comprende:

1. file che importano librerie di comunicazione;
2. funzioni contenenti primitive;
3. caller tree dei sink;
4. root raggiungibili;
5. statistiche sul grafo;
6. confidence degli archi;
7. fuzzy calls saltate;
8. limitazioni dell'analisi.

Il JSON comprende principalmente:

```text
comm_files
prims
funcs
edges
```

Il JSON deve essere considerato una rappresentazione intermedia dell'analisi.

---

# 24. Limiti

## Python dinamico

Non è possibile risolvere completamente:

```python
getattr(obj, name)
```

o:

```python
globals()[name]()
```

senza informazioni runtime.

---

## Dispatch

L'ereditarietà viene gestita in modo limitato e strutturale, ma non equivale a un runtime dispatch model completo.

---

## Decorator

Decorator che modificano significativamente la funzione possono rendere il call graph diverso da quello osservato staticamente.

---

## Monkey patching

Modifiche runtime a classi o moduli non vengono ricostruite.

---

## Import dinamici

Import effettuati tramite:

```python
importlib
__import__
```

non fanno parte del modello principale.

---

## Callback

I callback possono essere individuati come riferimenti, ma non tutti i percorsi di propagazione di un function object sono necessariamente rappresentati.

---

# 25. Relazione con `protocol_flow.py`

Questo script è il primo livello della pipeline.

Produce il modello necessario al secondo:

```text
comm_callgraph.py
        │
        ├── functions
        ├── call sites
        ├── edges
        └── communication primitives
                 │
                 ▼
        protocol_flow.py
```

Il secondo script utilizza direttamente il modello del primo.

Di conseguenza non sono due analizzatori completamente indipendenti.

---

# 26. API interna utilizzata dal Passo 2

`protocol_flow.py` utilizza direttamente elementi del modulo del Passo 1, tra cui:

```text
build_project
EXCLUDES
dotted
resolve
COMMON_NOISE
```

Questo significa che il primo script espone di fatto una **internal analysis API**, anche se non è ancora formalizzata come API pubblica.

Se il file viene rinominato, spostato o trasformato in package, questo contratto interno deve essere aggiornato.

---

# 27. Nota sull'import del modulo

Il secondo script importa:

```python
import sink_callergraph as cg
```

mentre il file documentato qui è denominato:

```text
comm_callgraph.py
```

Se `comm_callgraph.py` è realmente il nome fisico del modulo, l'import dovrà essere allineato.

Se invece `sink_callergraph.py` è il nome effettivo del modulo nel repository, questa documentazione descrive la sua funzione indipendentemente dal nome del file.

---

# 28. Interpretazione corretta

Il risultato deve essere letto come:

> "questo è ciò che il modello statico può ricostruire"

e non:

> "questo è sicuramente ciò che accade a runtime".

In particolare:

```text
exact
```

non significa "provato semanticamente".

Significa che la risoluzione è stata ottenuta tramite un'associazione statica diretta.

Analogamente:

```text
fuzzy
```

non significa "sbagliato".

Significa che l'associazione è euristica e deve essere trattata con maggiore cautela.

---

# 29. Esempio di utilizzo

Per un'analisi completa:

```bash
python comm_callgraph.py . \
    --kinds io,lifecycle,setup \
    --json callgraph.json
```

Per un'analisi più conservativa:

```bash
python comm_callgraph.py . \
    --strict \
    --no-tests \
    --json callgraph.json
```

Il risultato costituisce l'input concettuale per il Passo 2.
