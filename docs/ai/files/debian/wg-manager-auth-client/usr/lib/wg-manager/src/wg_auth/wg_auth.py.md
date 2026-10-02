# `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth.py`

## Metadata

- Path: `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth/wg_auth.py`
- Language: `python`
- Lines: 50
- SHA256: `43563bcd4f5e01c32b19cc43dd5cba8d9b01a7a61df6dc9d18c5f765162eec6a`
- Imports:
  - `configparser`
  - `logging`
  - `os`
  - `src.wg_auth.wg_auth_IPC`
  - `src.wg_auth.wg_auth_lifecycle`
  - `sys`
  - `threading`
  - `wg_auth_API`
  - `wg_auth_session`

## Source

```python
import configparser
import logging
import os
import sys
import threading

from src.wg_auth.wg_auth_IPC import WGAuthIPC
from src.wg_auth.wg_auth_lifecycle import WGAuthLifecycle
from wg_auth_session import WGAuthSession
from wg_auth_API import WGAuthAPI

log = logging.getLogger("wg-auth")
config_path = os.environ.get(
    "WG_AUTH_CONFIG",
    "/home/main/Desktop/wg_manager/config/wg-auth.conf",
)

def load_config(path):
    config = configparser.ConfigParser()
    config.read(path)

    return config

def main():

    config = load_config(config_path)

    lifecycle = WGAuthLifecycle(
        idle_timeout=config.getint(
            "client",
            "idle_timeout",
            fallback=45,
        ),
    )

    with WGAuthAPI(
        config,
        lifecycle,
    ) as api:

        lifecycle.api = api

        log.info("wg-auth API running")

        api.run()

    return 0

if __name__ == "__main__":
    sys.exit(main())
```
