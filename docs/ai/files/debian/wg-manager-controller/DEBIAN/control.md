# `debian/wg-manager-controller/DEBIAN/control`

## Metadata

- Path: `debian/wg-manager-controller/DEBIAN/control`
- Language: `unknown`
- Lines: 13
- SHA256: `f1f0efa758dd646e0778d789d9626d976c2ee2c40808ee301e4c48dbc6976451`

## Source

```
Package: wg-manager-controller
Source: wg-manager
Version: 0.1.0-5
Architecture: all
Maintainer: wg_manager local package <root@localhost>
Installed-Size: 44
Depends: python3, wireguard-tools, systemd, util-linux
Section: net
Priority: optional
Description: privileged WireGuard controller for wg_manager
 Provides the controller service that applies peer changes to a local
 WireGuard interface. It is intended for the host that owns the WireGuard
 interface and is separate from the authentication/frontend host.
```
