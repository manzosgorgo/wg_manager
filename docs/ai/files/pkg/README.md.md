# `pkg/README.md`

## Metadata

- Path: `pkg/README.md`
- Language: `markdown`
- Lines: 56
- SHA256: `32611737d321d7d0a70ee6769a975cf60cfdebbefc1d2d2179500ca070027299`

## Source

```markdown
# Debian packaging

Il packaging Debian usa debhelper e vive nella directory `debian/`.

Il source package `wg-manager` produce due binary package:

- `wg-manager-auth-client`: autenticazione OPAQUE, client per-sessione,
  frontend e integrazione Apache;
- `wg-manager-controller`: controller WireGuard privilegiato.

## Build

Dalla root della repository:

```bash
dpkg-buildpackage -us -uc -b
```

I file `debian/*.install` sono i manifest autorevoli dei file installati.

## Comportamento all'installazione

I package:

- creano gli utenti di sistema necessari;
- creano le directory runtime/state;
- installano configurazioni production sotto `/etc/wg-manager`;
- non installano certificati o private key;
- non abilitano e non avviano automaticamente i servizi.

Questo permette di completare configurazione e PKI prima del primo start.

## Tool installati

`wg-manager-auth-client` installa:

```text
/usr/sbin/wg-manager-users
/usr/sbin/wg-manager-check-auth-client
```

`wg-manager-controller` installa:

```text
/usr/sbin/wg-manager-check-controller
```

I checker sono read-only.

## Documentazione production

- [Deployment](../docs/deployment.md)
- [Configuration reference](../docs/configuration.md)

Le stesse guide vengono incluse sotto `/usr/share/doc/<package>/` nei
binary package.
```
