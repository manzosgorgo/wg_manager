#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SYSTEMD_DIR="/etc/systemd/system"
TMPFILES_DIR="/etc/tmpfiles.d"

if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must be run as root." >&2
    exit 1
fi

echo "[1/4] Installing wg-client systemd units"
install -m 0644 "$PROJECT_ROOT/systemd/wg-client-test@.service" "$SYSTEMD_DIR/wg-client-test@.service"
install -m 0644 "$PROJECT_ROOT/systemd/wg-client-test.socket" "$SYSTEMD_DIR/wg-client-test.socket"

echo "[2/4] Installing runtime directory configuration"
install -m 0644 "$PROJECT_ROOT/systemd/wg_client.conf" "$TMPFILES_DIR/wg_client.conf"
systemd-tmpfiles --create "$TMPFILES_DIR/wg_client.conf"

echo "[3/4] Reloading systemd and restarting socket"
systemctl daemon-reload
systemctl reset-failed
systemctl restart wg-client-test.socket

echo "[4/4] Installed state"
systemctl cat wg-client-test@.service wg-client-test.socket --no-pager
systemctl status wg-client-test.socket --no-pager
