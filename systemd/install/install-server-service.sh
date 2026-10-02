#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

if [ "$(id -u)" -ne 0 ]; then
    echo "This installer must be run as root." >&2
    exit 1
fi

echo "[1/3] Installing wg-manager systemd units"
install -m 0644 "$PROJECT_ROOT/systemd/wg-controller-test@.service" "$SYSTEMD_DIR/wg-controller-test@.service"
install -m 0644 "$PROJECT_ROOT/systemd/wg-controller-test.socket" "$SYSTEMD_DIR/wg-controller-test.socket"

echo "[2/3] Reloading systemd"
systemctl daemon-reload
systemctl reset-failed

echo "[3/3] Installed state"
systemctl cat wg-controller-test@.service wg-controller-test.socket --no-pager
systemctl status wg-controller-test.socket --no-pager || true
