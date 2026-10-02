import logging
import threading

log = logging.getLogger("wg_auth.lifecycle")


class WGAuthLifecycle:

    def __init__(self, api=None, ipc=None, idle_timeout=45):
        self.api = api
        self.ipc = ipc

        self.stop_event = threading.Event()
        self.shutdown_lock = threading.Lock()
        self.session_stop_event = threading.Event()

        self.idle_timeout = idle_timeout
        self._idle_timer = None

    def _cancel_idle_timer_locked(self):
        timer = self._idle_timer
        self._idle_timer = None

        if timer is not None:
            timer.cancel()

    def _arm_idle_timer_locked(self):
        self._cancel_idle_timer_locked()

        if self.idle_timeout <= 0:
            return

        timer = threading.Timer(
            self.idle_timeout,
            self._idle_timeout_expired,
        )
        timer.daemon = True
        self._idle_timer = timer
        timer.start()

    def _idle_timeout_expired(self):
        log.info("session idle timeout expired")
        self.request_session_shutdown()

    def touch_session(self):
        with self.shutdown_lock:
            if self.session_stop_event.is_set():
                return

            self._arm_idle_timer_locked()

        log.debug("session idle timer refreshed")

    def request_shutdown(self):
        with self.shutdown_lock:
            if self.stop_event.is_set():
                return

            self.stop_event.set()
            self._cancel_idle_timer_locked()
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
            self._cancel_idle_timer_locked()

        log.info("session shutdown requested")

        if self.api is not None:
            self.api.logout(notify_client=notify_client)

    def request_session_start(self):
        with self.shutdown_lock:
            self.session_stop_event.clear()
            self._arm_idle_timer_locked()

        log.info("session start requested")

        if self.ipc is not None:
            ipc_thread = threading.Thread(
                target=self.ipc.control_loop,
                name="wg-auth-ipc",
                daemon=True,
            )

            ipc_thread.start()
