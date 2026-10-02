#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must be run as root." >&2
    exit 1
fi

if ! getent passwd wg-auth >/dev/null; then
    echo "Missing system user: wg-auth" >&2
    exit 1
fi

if ! getent group wg-client >/dev/null; then
    echo "Missing system group: wg-client" >&2
    exit 1
fi

echo "[1/3] Installing wg-auth service"
install -m 0644 "$PROJECT_ROOT/systemd/wg-auth.service" "$SYSTEMD_DIR/wg-auth.service"

echo "[2/3] Reloading systemd"
systemctl daemon-reload
systemctl reset-failed

echo "[3/3] Installed state"
systemctl cat wg-auth.service --no-pager
systemctl status wg-auth.service --no-pager || true

echo
echo "Installed wg-auth.service."
echo "Start it with: systemctl start wg-auth.service"
echo "Enable it at boot with: systemctl enable wg-auth.service"
