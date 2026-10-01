import logging
import threading

log = logging.getLogger("wg_auth.lifecycle")
class WGAuthLifecycle:

    def __init__(self, api=None, ipc=None):
        self.api = api
        self.ipc = ipc

        self.stop_event = threading.Event()
        self.shutdown_lock = threading.Lock()
        self.session_stop_event = threading.Event()

    def request_shutdown(self):
        with self.shutdown_lock:
            if self.stop_event.is_set():
                return

            self.stop_event.set()
            log.info("shutdown requested")

            if self.api is not None:
                threading.Thread(
                    target=self.api.stop,
                    name="wg-auth-shutdown",
                    daemon=True,
                ).start()

    def request_session_shutdown(self, notify_client=True):
        with self.shutdown_lock:
            if self.session_stop_event.is_set():
                return

            self.session_stop_event.set()

        log.info("session shutdown requested")

        if self.api is not None:
            self.api.logout(notify_client=notify_client)

    def request_session_start(self):
        with self.shutdown_lock:
            self.session_stop_event.clear()

        log.info("session start requested")

        if self.ipc is not None:
            ipc_thread = threading.Thread(
                target=self.ipc.control_loop,
                name="wg-auth-ipc",
                daemon=True,
            )

            ipc_thread.start()