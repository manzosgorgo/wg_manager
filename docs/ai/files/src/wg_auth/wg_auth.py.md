# `src/wg_auth/wg_auth.py`

## Metadata

- Path: `src/wg_auth/wg_auth.py`
- Language: `python`
- Lines: 63
- SHA256: `1e38139d973d9d2eec2f1508513efe256e81a6a273f217055f8a193af90009f6`
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
"""
Process entry point for the wg-auth service.

Loads the INI configuration selected by WG_AUTH_CONFIG, builds the auth
lifecycle and HTTPS API, and serves until shutdown.
"""

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
    """
    Load and return the auth INI configuration from *path*.
    """
    config = configparser.ConfigParser()
    config.read(path)

    return config

def main():
    """
    Create the auth lifecycle and HTTPS API, then serve until shutdown.
    """

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
