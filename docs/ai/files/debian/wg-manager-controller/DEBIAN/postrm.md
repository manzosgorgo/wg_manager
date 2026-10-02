# `debian/wg-manager-controller/DEBIAN/postrm`

## Metadata

- Path: `debian/wg-manager-controller/DEBIAN/postrm`
- Language: `unknown`
- Lines: 18
- SHA256: `bdaa994fec5ef01db8e12defae366c720adb5347d05e64a98d36d11266a8b208`

## Source

```
#!/bin/sh
set -e

# Automatically added by dh_installsystemd/13.24.2
if [ "$1" = remove ] && [ -d /run/systemd/system ] ; then
	systemctl --system daemon-reload >/dev/null || true
fi
# End automatically added section
# Automatically added by dh_installsystemd/13.24.2
if [ "$1" = "purge" ]; then
	if [ -x "/usr/bin/deb-systemd-helper" ]; then
		deb-systemd-helper purge 'wg-manager.socket' >/dev/null || true
	fi
fi
# End automatically added section


exit 0
```
