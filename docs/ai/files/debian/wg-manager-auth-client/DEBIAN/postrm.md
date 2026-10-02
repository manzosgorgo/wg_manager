# `debian/wg-manager-auth-client/DEBIAN/postrm`

## Metadata

- Path: `debian/wg-manager-auth-client/DEBIAN/postrm`
- Language: `unknown`
- Lines: 27
- SHA256: `2cdfb66a055fa9b7ecc9ee9372b3f61d8c1db56febe689dcf5651c2cff6a5bc2`

## Source

```
#!/bin/sh
set -e

case "$1" in
    purge)
        if command -v a2disconf >/dev/null 2>&1; then
            a2disconf wg-manager >/dev/null 2>&1 || true
        fi
        ;;
esac

# debhelper inserts generated cleanup here.
# Automatically added by dh_installsystemd/13.24.2
if [ "$1" = remove ] && [ -d /run/systemd/system ] ; then
	systemctl --system daemon-reload >/dev/null || true
fi
# End automatically added section
# Automatically added by dh_installsystemd/13.24.2
if [ "$1" = "purge" ]; then
	if [ -x "/usr/bin/deb-systemd-helper" ]; then
		deb-systemd-helper purge 'wg-auth.service' 'wg-client.socket' >/dev/null || true
	fi
fi
# End automatically added section


exit 0
```
