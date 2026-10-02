# `debian/wg-manager-auth-client/DEBIAN/preinst`

## Metadata

- Path: `debian/wg-manager-auth-client/DEBIAN/preinst`
- Language: `unknown`
- Lines: 7
- SHA256: `9a628ef7c80f2e7e5c7104167de884421754679478c163d36a2b555bac647fb5`

## Source

```
#!/bin/sh
set -e
# Automatically added by dh_installsystemd/13.24.2
if [ -z "$DPKG_ROOT" ] && [ "$1" = upgrade ] && [ -d /run/systemd/system ] ; then
	deb-systemd-invoke stop 'wg-auth.service' 'wg-client.socket' >/dev/null || true
fi
# End automatically added section
```
