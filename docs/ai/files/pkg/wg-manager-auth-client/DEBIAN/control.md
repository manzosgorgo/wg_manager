# `pkg/wg-manager-auth-client/DEBIAN/control`

## Metadata

- Path: `pkg/wg-manager-auth-client/DEBIAN/control`
- Language: `unknown`
- Lines: 11
- SHA256: `32c47ade26497f64331e44f74b5eac242881b028b51ce7e24575870b39273bcd`

## Source

```
Package: wg-manager-auth-client
Version: 0.1.0-1
Section: net
Priority: optional
Architecture: all
Maintainer: wg_manager local package <root@localhost>
Depends: python3, python3-opaque, python3-systemd, apache2, systemd, util-linux
Description: wg_manager authentication, session client and web frontend
 Provides the OPAQUE authentication service, per-session wg-client service,
 browser frontend and Apache reverse-proxy integration for wg_manager.
 This package does not include the privileged WireGuard controller.
```
