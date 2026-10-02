# `debian/control`

## Metadata

- Path: `debian/control`
- Language: `unknown`
- Lines: 24
- SHA256: `641e9c94f0807c0de21a0fc46879eaf371727729e470c8375ac54c37ca67885b`

## Source

```
Source: wg-manager
Section: net
Priority: optional
Maintainer: wg_manager local package <root@localhost>
Build-Depends: debhelper-compat (= 13)
Standards-Version: 4.7.2
Rules-Requires-Root: no

Package: wg-manager-auth-client
Architecture: all
Depends: ${misc:Depends}, python3, python3-opaque, python3-systemd, python3-cryptography, apache2, systemd, util-linux
Description: authentication, session client and web frontend for wg_manager
 Provides the OPAQUE authentication service, per-session wg-client service,
 browser frontend and Apache reverse-proxy integration for wg_manager.
 This package is intended for the authentication/frontend host and does not
 include the privileged WireGuard controller.

Package: wg-manager-controller
Architecture: all
Depends: ${misc:Depends}, python3, wireguard-tools, systemd, util-linux
Description: privileged WireGuard controller for wg_manager
 Provides the controller service that applies peer changes to a local
 WireGuard interface. It is intended for the host that owns the WireGuard
 interface and is separate from the authentication/frontend host.
```
