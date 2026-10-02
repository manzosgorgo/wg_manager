# TODO — wg_manager

Questa lista contiene solo lavoro ancora aperto dopo la revisione
`protocol-review`.

## Prossima fase: frontend

- Implementare il frontend completo sopra il flow OPAQUE esistente.
- Visualizzare i peer dell'utente con stato runtime.
- Aggiungere provisioning tramite QR code e file WireGuard.
- Aggiungere pagina admin con:
  - lista peer;
  - public key e allowed IP;
  - endpoint/handshake/RX/TX;
  - owner;
  - stato `consistent/orphan/stale`;
  - reassignment owner;
  - create/delete account.
- Usare l'indice IP per proporre indirizzi disponibili senza esporre
  inutilmente i peer degli altri utenti.

## Hardening successivo

- Valutare un protocollo applicativo autenticato anche sul collegamento
  `wg-client -> wg-manager`, oltre all'mTLS già presente.
- Riesaminare crash consistency tra persistence e modifica WireGuard dopo che
  il sistema completo frontend/backend è stabile.
- Valutare recovery/migration UX per stati `orphan` e `stale`.

## Deployment / configurazione

- Separare progressivamente le configurazioni di test da quelle di
  produzione.
- Eliminare i path assoluti di sviluppo dalle unit systemd quando verrà
  definita la procedura di installazione definitiva.
- Verificare il profilo di hardening systemd finale per `wg-auth`,
  `wg-client` e `wg-manager`.
- Definire install/update della PKI e rotazione certificati.

## Documentazione

- Mantenere `README.md` come descrizione normativa ad alto livello.
- Rigenerare `docs/ai/**` dopo modifiche di protocollo o comunicazione.
- Non modificare manualmente gli artefatti generati sotto `docs/ai/`.
- Aggiornare questa TODO solo con attività ancora realmente aperte.
