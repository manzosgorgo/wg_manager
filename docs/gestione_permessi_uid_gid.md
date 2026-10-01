Sì, questa è una separazione molto più pulita: **`wg-manager` e `wg-client` sono identità di servizio distinte**, e in sviluppo `main` può appartenere a entrambi i gruppi. In questo modo non devi fare `sudo`, `setuid` o cambiare utente.

La situazione attuale è:

```text
/run/wg_manager/
└── wg-client-test.sock
    root:root
    srw-------
```

quindi il problema è esattamente il socket: **solo root può leggerlo/scriverlo**.

Ti proporrei di fare le modifiche in quest'ordine.

### 1. Creare i due gruppi/utenti di servizio

Sulla macchina dove gira `wg-manager`:

```bash
sudo groupadd wg-manager
sudo useradd --system --gid wg-manager --no-create-home --shell /usr/sbin/nologin wg-manager
```

Sulla macchina dove gira `wg-client`:

```bash
sudo groupadd wg-client
sudo useradd --system --gid wg-client --no-create-home --shell /usr/sbin/nologin wg-client
```

Se gli utenti esistono già, ovviamente **non ricrearli**.

L'idea finale è:

```text
manager machine              client machine

wg-manager:wg-manager        wg-client:wg-client
       │                            │
       │                            │
       └────── comunicazione ──────┘
```

---

### 2. In sviluppo aggiungere `main` ai due gruppi

Sulla macchina di sviluppo:

```bash
sudo usermod -aG wg-manager main
sudo usermod -aG wg-client main
```

Controlla:

```bash
groups main
```

Dovresti vedere entrambi:

```text
... wg-manager wg-client
```

**Attenzione:** la shell/sessione già aperta non acquisisce automaticamente i nuovi gruppi.

Puoi fare logout/login oppure, per la shell corrente:

```bash
newgrp wg-manager
```

ma per avere entrambi i gruppi in modo normale è preferibile fare logout/login.

---

### 3. Decidere chi deve possedere il socket

Per il socket di `wg-client`, il proprietario dovrebbe essere:

```text
wg-client:wg-client
```

Non `root:root`.

Quindi vogliamo arrivare a:

```text
srw-rw---- wg-client wg-client wg-client-test.sock
```

ovvero:

```text
0660
```

Il significato è:

```text
owner  → rw
group  → rw
others → ---
```

Così:

```text
wg-client  → può usarlo
main       → può usarlo perché appartiene a wg-client
altri      → no
```

---

### 4. Modificare il `.socket` di systemd

Nel file:

```text
wg-client-test.socket
```

nella sezione `[Socket]` metti esplicitamente:

```ini
[Socket]
ListenStream=/run/wg_manager/wg-client-test.sock
SocketUser=wg-client
SocketGroup=wg-client
SocketMode=0660
```

La parte importante è:

```ini
SocketUser=wg-client
SocketGroup=wg-client
SocketMode=0660
```

Questo è preferibile a fare un `chmod` manuale sul socket, perché **systemd ricreerà il socket correttamente ad ogni avvio**.

---

### 5. Ricaricare systemd

```bash
sudo systemctl daemon-reload
```

Poi riavvia il socket:

```bash
sudo systemctl restart wg-client-test.socket
```

Se il servizio associato è già attivo e vuoi essere sicuro di ripartire pulito:

```bash
sudo systemctl stop wg-client-test.service
sudo systemctl restart wg-client-test.socket
```

Nel caso di `Accept=yes`, il service instance viene poi creato quando arriva una connessione.

---

### 6. Controllare immediatamente il risultato

```bash
ls -la /run/wg_manager/
```

Vogliamo vedere qualcosa del genere:

```text
srw-rw---- 1 wg-client wg-client 0 ... wg-client-test.sock
```

Ancora meglio:

```bash
stat /run/wg_manager/wg-client-test.sock
```

e controllare:

```text
Uid: ... (wg-client)
Gid: ... (wg-client)
Access: (0660/srw-rw----)
```

---

### 7. Verificare l'accesso come `wg-client`

Prima proviamo l'identità reale del servizio:

```bash
sudo -u wg-client ls -l /run/wg_manager/wg-client-test.sock
```

e poi, soprattutto, proviamo effettivamente ad aprire/usare il socket con il tuo activator:

```bash
sudo -u wg-client ./test_wg_client_activator.py
```

oppure il comando che usi normalmente.

Questo deve funzionare **senza root**.

---

### 8. Verificare l'accesso come `main`

Dopo aver acquisito il gruppo `wg-client`:

```bash
ls -l /run/wg_manager/wg-client-test.sock
```

e poi direttamente:

```bash
./test_wg_client_activator.py
```

senza:

```bash
sudo
```

Questo è proprio il test architetturalmente importante: **lo sviluppatore non deve avere bisogno di diventare `wg-client`**.

---

### 9. Controllare anche il percorso completo

Hai già verificato che:

```text
/run/wg_manager
drwxr-xr-x root root
```

è attraversabile da tutti, quindi **al momento non è un problema**.

Puoi comunque fare il controllo completo:

```bash
namei -l /run/wg_manager/wg-client-test.sock
```

Dovresti ottenere qualcosa del tipo:

```text
drwxr-xr-x root root /
drwxr-xr-x root root run
drwxr-xr-x root root wg_manager
srw-rw---- wg-client wg-client wg-client-test.sock
```

La cosa fondamentale è che ogni directory nel percorso abbia il bit `x` per l'utente che deve raggiungere il socket.

Nel tuo caso è già così.

---

### 10. Alla fine avrai questa struttura

In produzione:

```text
wg-manager machine
        │
        └── wg-manager:wg-manager


wg-client machine
        │
        └── wg-client:wg-client
```

In sviluppo, invece:

```text
                    main
                   /    \
                  /      \
         wg-manager     wg-client
              │              │
              │              │
          manager          client
```

Quindi `main` può accedere alle risorse di entrambi senza cambiare UID.

E soprattutto il socket diventa:

```text
/run/wg_manager/wg-client-test.sock
        │
        ├── owner:  wg-client
        ├── group:  wg-client
        └── mode:   0660
```

che è esattamente il modello che vorrei anche per il futuro `wg_auth`: **`wg_auth` potrà essere un processo non-root, membro del gruppo appropriato, e parlare con `wg-client` tramite Unix socket senza nessun meccanismo di privilege escalation**.

Una piccola nota: **non modificherei ancora le directory**, visto che dai permessi che hai mostrato sono già corrette. Cambierei prima solo ownership/mode del socket tramite il `.socket` di systemd e verificherei il comportamento.
