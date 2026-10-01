# `systemd/install/install-server-service.sh`

## Metadata

- Path: `systemd/install/install-server-service.sh`
- Language: `bash`
- Lines: 7
- SHA256: `6a363244597afcb1c0447ff689af4fa45a9d68c9fc0400ad57186e7cc153bf8b`

## Source

```bash
#!/bin/bash

cp /home/main/Desktop/wg_manager/systemd/wg-controller-test@.service /home/main/Desktop/wg_manager/systemd/wg-controller-test.socket  /etc/systemd/system
systemctl daemon-reload
systemctl reset-failed
systemctl cat wg-controller-test@.service wg-controller-test.socket --no-pager
systemctl status wg-controller-test@\*.service wg-controller-test.socket --no-pager
```
