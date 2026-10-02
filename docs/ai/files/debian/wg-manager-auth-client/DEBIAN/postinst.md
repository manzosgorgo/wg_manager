# `debian/wg-manager-auth-client/DEBIAN/postinst`

## Metadata

- Path: `debian/wg-manager-auth-client/DEBIAN/postinst`
- Language: `unknown`
- Lines: 94
- SHA256: `6e376afd9bb27cf1506334dcd3a1e51c8d21104ac539ce38257dba458d83e728`

## Source

```
#!/bin/sh
set -e

case "$1" in
    configure)
        if command -v systemd-sysusers >/dev/null 2>&1; then
            systemd-sysusers /usr/lib/sysusers.d/wg-manager-auth-client.conf
        fi

        if command -v a2enmod >/dev/null 2>&1; then
            a2enmod alias proxy proxy_http ssl >/dev/null
        fi
        ;;
esac

# debhelper inserts sysusers/tmpfiles/systemd integration here.
# Automatically added by dh_installtmpfiles/13.24.2
if [ "$1" = "configure" ] || [ "$1" = "abort-upgrade" ] || [ "$1" = "abort-deconfigure" ] || [ "$1" = "abort-remove" ] ; then
	if [ -x "$(command -v systemd-tmpfiles)" ]; then
		systemd-tmpfiles ${DPKG_ROOT:+--root="$DPKG_ROOT"} --create wg-manager-auth-client.conf || true
	fi
fi
# End automatically added section
# Automatically added by dh_installsystemd/13.24.2
if [ "$1" = "configure" ] || [ "$1" = "abort-upgrade" ] || [ "$1" = "abort-deconfigure" ] || [ "$1" = "abort-remove" ] ; then
	if deb-systemd-helper debian-installed 'wg-auth.service'; then
		# The following line should be removed in trixie or trixie+1
		deb-systemd-helper unmask 'wg-auth.service' >/dev/null || true

		if deb-systemd-helper --quiet was-enabled 'wg-auth.service'; then
			# Create new symlinks, if any.
			deb-systemd-helper enable 'wg-auth.service' >/dev/null || true
		fi
	fi

	# Update the statefile to add new symlinks (if any), which need to be cleaned
	# up on purge. Also remove old symlinks.
	deb-systemd-helper update-state 'wg-auth.service' >/dev/null || true
fi
# End automatically added section
# Automatically added by dh_installsystemd/13.24.2
if [ "$1" = "configure" ] || [ "$1" = "abort-upgrade" ] || [ "$1" = "abort-deconfigure" ] || [ "$1" = "abort-remove" ] ; then
	if deb-systemd-helper debian-installed 'wg-client.socket'; then
		# The following line should be removed in trixie or trixie+1
		deb-systemd-helper unmask 'wg-client.socket' >/dev/null || true

		if deb-systemd-helper --quiet was-enabled 'wg-client.socket'; then
			# Create new symlinks, if any.
			deb-systemd-helper enable 'wg-client.socket' >/dev/null || true
		fi
	fi

	# Update the statefile to add new symlinks (if any), which need to be cleaned
	# up on purge. Also remove old symlinks.
	deb-systemd-helper update-state 'wg-client.socket' >/dev/null || true
fi
# End automatically added section


if [ "$1" = "configure" ]; then
    install -d -o wg-auth -g wg-auth -m 0700 /var/lib/wg-manager/auth

    install -d -o root -g root      -m 0755 /etc/wg-manager/cert
    install -d -o root -g wg-auth   -m 0750 /etc/wg-manager/cert/auth
    install -d -o root -g wg-client -m 0750 /etc/wg-manager/cert/client
    install -d -o root -g www-data  -m 0750 /etc/wg-manager/cert/apache

    if [ -e /etc/wg-manager/cert/ca.crt ]; then
        chown root:root /etc/wg-manager/cert/ca.crt
        chmod 0644 /etc/wg-manager/cert/ca.crt
    fi
    if [ -e /etc/wg-manager/cert/auth/auth.crt ]; then
        chown root:wg-auth /etc/wg-manager/cert/auth/auth.crt
        chmod 0644 /etc/wg-manager/cert/auth/auth.crt
    fi
    if [ -e /etc/wg-manager/cert/auth/auth.key ]; then
        chown root:wg-auth /etc/wg-manager/cert/auth/auth.key
        chmod 0640 /etc/wg-manager/cert/auth/auth.key
    fi
    if [ -e /etc/wg-manager/cert/client/client.crt ]; then
        chown root:wg-client /etc/wg-manager/cert/client/client.crt
        chmod 0644 /etc/wg-manager/cert/client/client.crt
    fi
    if [ -e /etc/wg-manager/cert/client/client.key ]; then
        chown root:wg-client /etc/wg-manager/cert/client/client.key
        chmod 0640 /etc/wg-manager/cert/client/client.key
    fi
    if [ -e /etc/wg-manager/cert/apache/apache-client.pem ]; then
        chown root:www-data /etc/wg-manager/cert/apache/apache-client.pem
        chmod 0640 /etc/wg-manager/cert/apache/apache-client.pem
    fi
fi

exit 0
```
