# `apache/install/install-apache.sh`

## Metadata

- Path: `apache/install/install-apache.sh`
- Language: `bash`
- Lines: 37
- SHA256: `e5dc9004f46412622637e4736939660e019da907e318a9ab1a0e0a2dfd39153e`

## Source

```bash
#!/bin/bash
set -e

PROJECT_ROOT="/home/main/Desktop/wg_manager"
APACHE_CONF_SRC="$PROJECT_ROOT/apache/wg-manager.conf"
APACHE_CONF_DST="/etc/apache2/conf-available/wg-manager.conf"
APACHE_CLIENT_PEM="/etc/apache2/wg-manager-proxy-client.pem"

if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must be run as root."
    exit 1
fi

echo "[1/5] Enabling Apache modules"
a2enmod alias proxy proxy_http ssl

echo "[2/5] Installing wg_manager Apache configuration"
cp "$APACHE_CONF_SRC" "$APACHE_CONF_DST"

echo "[3/5] Installing proxy client certificate"
cat     "$PROJECT_ROOT/cert/client.crt"     "$PROJECT_ROOT/cert/client.key"     > "$APACHE_CLIENT_PEM"

chown root:root "$APACHE_CLIENT_PEM"
chmod 600 "$APACHE_CLIENT_PEM"

echo "[4/5] Enabling configuration"
a2enconf wg-manager

echo "[5/5] Validating and reloading Apache"
apachectl configtest
systemctl reload apache2

echo
echo "wg_manager Apache configuration installed."
echo "Frontend: http://127.0.0.1/vpn/"
echo "Auth proxy: /auth, /auth/verify, /status"
echo "Client proxy: /postauth/"
```
