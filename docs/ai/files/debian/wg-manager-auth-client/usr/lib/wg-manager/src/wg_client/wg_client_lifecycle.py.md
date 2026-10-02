# `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_lifecycle.py`

## Metadata

- Path: `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client/wg_client_lifecycle.py`
- Language: `python`
- Lines: 56
- SHA256: `f6815a006fb7b11dd42948071cc8807dfbacbe9abd679e9aebeefd5c144136c0`
- Imports:
  - `logging`
  - `threading`

## Source

```python
import logging
import threading

log = logging.getLogger("wg_client.lifecycle")
class WGClientLifecycle:
    def __init__(self, api=None, ipc=None):
        self.api = api
        self.ipc = ipc

        self.stop_event = threading.Event()
        self.shutdown_lock = threading.Lock()

    def notify_activity(self):
        ipc = self.ipc
        if ipc is None:
            return

        ipc.keepalive()

    def request_shutdown(self, notify_shutdown=True):
        with self.shutdown_lock:
            if self.stop_event.is_set():
                return

            self.stop_event.set()

        log.info("shutdown requested")

        # Da qui in poi NON teniamo più shutdown_lock.
        #
        # Qualunque cosa succeda durante il cleanup,
        # dobbiamo continuare con le fasi successive.

        if self.ipc is not None:
            log.debug("requesting ipc shutdown")

            try:
                self.ipc.stop(notify_shutdown)
            except OSError as exc:
                log.warning(
                    "IPC shutdown failed: %s",
                    exc,
                )
            except Exception:
                log.exception(
                    "unexpected error during IPC shutdown"
                )

        if self.api is not None:
            log.debug("requesting api shutdown")

            threading.Thread(
                target=self.api.stop,
                name="wg-client-shutdown",
                daemon=True,
            ).start()
```
