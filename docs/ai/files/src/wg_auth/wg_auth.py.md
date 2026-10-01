# `src/wg_auth/wg_auth.py`

## Metadata

- Path: `src/wg_auth/wg_auth.py`
- Language: `python`
- Lines: 39
- SHA256: `4b47f635f1af649b3db5b1ad4d768956b988b8ce2caaf454943c114cd0ece4c8`
- Imports:
  - `configparser`
  - `logging`
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
import sys
import threading

from src.wg_auth.wg_auth_IPC import WGAuthIPC
from src.wg_auth.wg_auth_lifecycle import WGAuthLifecycle
from wg_auth_session import WGAuthSession
from wg_auth_API import WGAuthAPI

log = logging.getLogger("wg-auth")
config_path = "/home/main/Desktop/wg_manager/config/wg-auth.conf"
def load_config(path):
    config = configparser.ConfigParser()
    config.read(path)

    return config

def main():

    config = load_config(config_path)

    lifecycle = WGAuthLifecycle()

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
