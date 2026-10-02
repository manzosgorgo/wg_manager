# `debian/wg-manager-auth-client/usr/sbin/wg-manager-users`

## Metadata

- Path: `debian/wg-manager-auth-client/usr/sbin/wg-manager-users`
- Language: `unknown`
- Lines: 17
- SHA256: `70891f3885ebbc48abdb22398880c78f2c1d90cbabc795113ed3fc4db987d238`

## Source

```
#!/bin/sh
set -e

TOOL=/usr/lib/wg-manager/tools/manage_users.py
LOGIN_DIR=/var/lib/wg-manager/auth

if [ "$(id -u)" -eq 0 ]; then
    exec /usr/sbin/runuser -u wg-auth -- \
        /usr/bin/python3 "$TOOL" --login-dir "$LOGIN_DIR" "$@"
fi

if [ "$(id -un)" = "wg-auth" ]; then
    exec /usr/bin/python3 "$TOOL" --login-dir "$LOGIN_DIR" "$@"
fi

echo "wg-manager-users must be run as root or wg-auth" >&2
exit 1
```
