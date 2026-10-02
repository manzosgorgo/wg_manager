# `pkg/wg-manager-controller/DEBIAN/control`

## Metadata

- Path: `pkg/wg-manager-controller/DEBIAN/control`
- Language: `unknown`
- Lines: 11
- SHA256: `447e7452340aec3a41dbed23a41da2dadca5c13574cbe9aa9677345a947c5da3`

## Source

```
Package: wg-manager-controller
Version: 0.1.0-1
Section: net
Priority: optional
Architecture: all
Maintainer: wg_manager local package <root@localhost>
Depends: python3, wireguard-tools, systemd
Description: privileged WireGuard controller for wg_manager
 Provides the wg_manager controller service that applies peer changes to a
 local WireGuard interface. It is intended for the host that owns the
 WireGuard interface and is separate from the authentication/frontend host.
```
