# `debian/wg-manager-auth-client/DEBIAN/control`

## Metadata

- Path: `debian/wg-manager-auth-client/DEBIAN/control`
- Language: `unknown`
- Lines: 14
- SHA256: `3c9395a9c8dec768d2de969a775212e6620a8226399e140ee2f93646d7a32978`

## Source

```
Package: wg-manager-auth-client
Source: wg-manager
Version: 0.1.0-5
Architecture: all
Maintainer: wg_manager local package <root@localhost>
Installed-Size: 654
Depends: python3, python3-opaque, python3-systemd, python3-cryptography, apache2, systemd, util-linux
Section: net
Priority: optional
Description: authentication, session client and web frontend for wg_manager
 Provides the OPAQUE authentication service, per-session wg-client service,
 browser frontend and Apache reverse-proxy integration for wg_manager.
 This package is intended for the authentication/frontend host and does not
 include the privileged WireGuard controller.
```
