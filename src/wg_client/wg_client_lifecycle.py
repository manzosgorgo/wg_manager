"""
Lifecycle coordination for one wg-client session.

Activity is reported back to wg-auth as KEEPALIVE; shutdown stops the IPC
channel and asks the HTTPS server to leave serve_forever without holding the
shutdown lock during cleanup.
"""

import logging
import threading

log = logging.getLogger("wg_client.lifecycle")
class WGClientLifecycle:
    """
    Coordinate keepalive activity and one-shot shutdown of IPC and HTTPS layers.
    """
    def __init__(self, api=None, ipc=None):
        """
        Create lifecycle state for an optional API and IPC channel.
        """
        self.api = api
        self.ipc = ipc

        self.stop_event = threading.Event()
        self.shutdown_lock = threading.Lock()

    def notify_activity(self):
        """
        Send a best-effort KEEPALIVE to wg-auth when IPC is available.
        """
        ipc = self.ipc
        if ipc is None:
            return

        ipc.keepalive()

    def request_shutdown(self, notify_shutdown=True):
        """
        Request session shutdown once and stop IPC/API without holding the lifecycle lock.
        """
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