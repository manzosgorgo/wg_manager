# `systemd/install/install-server-service.sh`

## Metadata

- Path: `systemd/install/install-server-service.sh`
- Language: `bash`
- Lines: 22
- SHA256: `f1645759036844eddb22d5e47ab16a9f73aff5d5265250b1f1e8590c7f399a59`

## Source

```bash
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
```
