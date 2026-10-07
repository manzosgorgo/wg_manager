# Deployment dei package Debian

Questa è la guida operativa per installare e configurare `wg_manager` dai
package Debian. La documentazione sotto `docs/ai/` è generata
meccanicamente e non sostituisce questa guida.

## Ruoli e package

Il progetto produce due package indipendenti:

- `wg-manager-auth-client`: installa `wg-auth`, il client per-sessione,
  il frontend web e la configurazione Apache;
- `wg-manager-controller`: installa il controller privilegiato che modifica
  l'interfaccia WireGuard.

I due package possono essere installati sulla stessa macchina per test, ma il
deployment previsto consente di tenere il controller su un host separato.

## Build

Dalla root della repository:

```bash
dpkg-buildpackage -us -uc -b
```

I package vengono creati nella directory superiore alla repository.

## Installazione

Host auth/frontend:

```bash
sudo apt install ../wg-manager-auth-client_<version>_all.deb
```

Host controller:

```bash
sudo apt install ../wg-manager-controller_<version>_all.deb
```

I servizi vengono installati intenzionalmente disabilitati e non vengono
avviati durante l'installazione. Prima vanno configurati i certificati e i
parametri specifici della rete.

## File principali

### Host auth/frontend

```text
/etc/wg-manager/wg-auth.conf
/etc/wg-manager/wg-client.conf
/etc/apache2/conf-available/wg-manager.conf

/etc/wg-manager/cert/ca.crt
/etc/wg-manager/cert/auth/auth.crt
/etc/wg-manager/cert/auth/auth.key
/etc/wg-manager/cert/client/client.crt
/etc/wg-manager/cert/client/client.key
/etc/wg-manager/cert/apache/apache-client.pem

/var/lib/wg-manager/auth/
/run/wg-manager/
```

### Host controller

```text
/etc/wg-manager/wg-manager.conf

/etc/wg-manager/cert/ca.crt
/etc/wg-manager/cert/controller/server.crt
/etc/wg-manager/cert/controller/server.key
```

La reference completa dei parametri è in
[`docs/configuration.md`](configuration.md).

## 1. Certificati

I package non contengono certificati né private key. Copiarli dalla PKI nelle
directory indicate sopra.

Permessi attesi sull'host auth/frontend:

```text
ca.crt                         root:root       0644
auth/auth.crt                  root:wg-auth    0644
auth/auth.key                  root:wg-auth    0640
client/client.crt              root:wg-client  0644
client/client.key              root:wg-client  0640
apache/apache-client.pem       root:www-data   0640
```

Permessi attesi sull'host controller:

```text
ca.crt                         root:root        0644
controller/server.crt          root:wg-manager  0644
controller/server.key          root:wg-manager  0640
```

Le directory vengono già create dal package col gruppo corretto.

## 2. Configurazione host auth/frontend

Editare:

```text
/etc/wg-manager/wg-client.conf
```

Almeno questi valori devono essere adattati:

```ini
[controller]
host = <IP o DNS del controller>

[wireguard]
interface = wg0
endpoint = <endpoint pubblico WireGuard>:51820
```

Controllare anche `/etc/wg-manager/wg-auth.conf` se si vogliono cambiare
porte, timeout o path.

Verifica automatica:

```bash
sudo wg-manager-check-auth-client
```

## 3. Creazione dell'account amministratore

Il package non crea password predefinite.

Creare il primo account:

```bash
sudo wg-manager-users create admin
```

Il comando esegue la scrittura come utente di sistema `wg-auth`, quindi i
record OPAQUE vengono creati con ownership corretta sotto
`/var/lib/wg-manager/auth`.

Per utenti successivi:

```bash
sudo wg-manager-users create NOME
sudo wg-manager-users delete NOME
```

## 4. Configurazione host controller

Editare:

```text
/etc/wg-manager/wg-manager.conf
```

Controllare almeno:

```ini
[manager]
interface = wg0

[policy]
vpn_network = 10.20.0.0/24
server_address = 10.20.0.1/32
```

Il socket controller ascolta sulla porta TCP 9443. La reachability e il
firewall devono essere configurati in modo coerente con la rete che collega
`wg-client` al controller.

Verifica automatica:

```bash
sudo wg-manager-check-controller
```

## 5. Avvio controller

Dopo che configurazione e certificati sono pronti:

```bash
sudo systemctl enable --now wg-manager.socket
```

Controllare:

```bash
systemctl status wg-manager.socket
journalctl -u 'wg-manager@*'
```

## 6. Apache e servizi auth/client

Il package installa la configurazione Apache ma non la abilita automaticamente,
perché richiede i certificati.

Verificare prima:

```bash
sudo apachectl configtest
```

Poi:

```bash
sudo a2enconf wg-manager
sudo systemctl reload apache2
```

Infine avviare `wg-auth`:

```bash
sudo systemctl enable --now wg-auth.service
```

`wg-auth.service` richiede `wg-client.socket`, che viene quindi avviato
automaticamente. Le istanze `wg-client@.service` vengono create via socket
activation quando serve una sessione.

Controllare:

```bash
systemctl status wg-auth.service wg-client.socket
journalctl -u wg-auth.service
journalctl -u 'wg-client@*'
```

## 7. Checklist finale

Host controller:

```bash
sudo wg-manager-check-controller
```

Host auth/frontend:

```bash
sudo wg-manager-check-auth-client
```

Entrambi i checker sono read-only: non modificano configurazioni, certificati,
firewall o stato dei servizi.

## Upgrade

Ricostruire e installare la nuova versione con `apt install ./file.deb`.
I file sotto `/etc` sono configurazioni del package e non devono essere
sostituiti alla cieca durante gli upgrade.

Dopo un upgrade controllare sempre:

```bash
sudo wg-manager-check-auth-client
sudo wg-manager-check-controller
```

eseguendo naturalmente solo il checker relativo ai package installati.
