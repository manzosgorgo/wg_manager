# `debian/wg-manager-controller/DEBIAN/preinst`

## Metadata

- Path: `debian/wg-manager-controller/DEBIAN/preinst`
- Language: `unknown`
- Lines: 7
- SHA256: `750aa0caf5598765217d474e2ae5ca51c47e5268c054b7af6d2e9ab7ea92aba6`

## Source

```
#!/bin/sh
set -e
# Automatically added by dh_installsystemd/13.24.2
if [ -z "$DPKG_ROOT" ] && [ "$1" = upgrade ] && [ -d /run/systemd/system ] ; then
	deb-systemd-invoke stop 'wg-manager.socket' >/dev/null || true
fi
# End automatically added section
```
