#!/usr/bin/env python3

import logging
import os
import re
import socket
import sys
import threading
import time

from systemd import journal

from src.wg_client.wg_client_API import WGClientAPI
from src.wg_client.wg_client_IPC import WGClientIPC
from src.wg_client.wg_client_errors import WGError
from src.wg_client.wg_client_config import load_config
from src.wg_client.wg_client_lifecycle import WGClientLifecycle
from src.wg_client.wg_secure_session import WGSecureSession



# Every module logs below "wg_manager"; the journal handler
# is attached once, in setup_logging().
log = logging.getLogger("wg_manager.client")


def setup_logging():
    handler = journal.JournalHandler(SYSLOG_IDENTIFIER="wg_client")
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))

    root = logging.getLogger("wg_manager")
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)


def systemd_notify(message):
    notify_socket = os.environ.get("NOTIFY_SOCKET")

    if not notify_socket:
        return False

    if notify_socket.startswith("@"):
        notify_socket = "\0" + notify_socket[1:]

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        sock.connect(notify_socket)
        sock.sendall(message.encode())
        return True
    finally:
        sock.close()


def activate(ipc, lifecycle):
    """
    Read the activation packet and bring the HTTPS API up.

    Sends ACTIVATION_RESULT only once the API socket is bound and
    TLS is ready, so "OK" means the API is actually reachable.
    Returns (api, activation), or None on failure.
    :param lifecycle:
    """
    api = None

    try:
        log.debug("activate waiting for activation packet")

        packet = ipc.receive_packet()

        log.debug("received packet of %d bytes", len(packet))

        activation = ipc.parse_activation(ipc.parse_packet(packet))

        # Never log k_session.
        log.info(
            "received activation packet: session_id=%s client_id=%r expires_at=%d,listen_path=%s",
            activation["session_id"].hex(),
            activation["client_id"],
            activation["expires_at"],
            activation["listen_path"]
        )

        cfg = load_config()
        log.info("wg_client parsed config file")

        session = WGSecureSession(
            cfg,
            activation["k_session"],
            activation["session_id"],
            principal=activation["principal"],
        )

        if cfg["secure_session"]["enabled"] is not True:
            raise RuntimeError("secure session cannot be disabled")

        log.info("wg_client using secure session")
        api = WGClientAPI(
            cfg,
            activation["listen_path"],
            session,
            lifecycle,
        )

        log.debug("api bind")
        api.bind()

    except Exception as exc:
        # Activation is an IPC request/response boundary. Any ordinary
        # exception must be reported to wg-auth as ACTIVATION_RESULT ERROR;
        # otherwise the process exits and auth only observes an ambiguous EOF.
        log.exception("activation failed")

        if api is not None:
            api.close()

        try:
            ipc.send_result("ERROR", error=str(exc))
        except OSError:
            pass

        return None

    try:
        ipc.send_result("OK", expires_at=activation["expires_at"])

    except OSError as exc:
        # Nobody learned about this session: do not serve it.
        log.error("cannot send activation result: %s", exc)
        api.close()
        return None

    log.info("activation result sent")

    return api, activation


def main():
    setup_logging()
    log.info("wg_client starting")

    # systemd Accept=yes passes the accepted connection on stdin
    # (StandardInput=socket).
    sock = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
        fileno=os.dup(sys.stdin.fileno())
    )
    lifecycle = WGClientLifecycle()
    ipc = WGClientIPC(sock, lifecycle)
    result = activate(ipc,lifecycle)
    lifecycle.ipc = ipc

    if result is None:
        return 1

    api, activation = result

    remaining = activation["expires_at"] - time.time()

    # stop() makes serve() return even if it fires before
    # serve_forever() starts looping.
    timer = threading.Timer(max(remaining, 0), lifecycle.request_shutdown)
    timer.daemon = True
    timer.start()

    ipc_thread = threading.Thread(
        target=ipc.control_loop,
        name="wg-client-ipc",
    )
    ipc_thread.start()

    systemd_notify("READY=1")
    systemd_notify(f"STATUS=session_id={activation['session_id']}")
    log.info("wg_client is READY")

    try:
        api.serve()

    except WGError as exc:
        log.error("API error: %s", exc)
        return 1

    finally:
        timer.cancel()
        systemd_notify("STOPPING=1")
        log.debug("wg_client stopped")

        devnull = os.open(os.devnull, os.O_RDONLY)
        os.dup2(devnull, sys.stdin.fileno())
        os.close(devnull)


    log.info("session expired")

    for thread in threading.enumerate():
        log.warning(
            "THREAD: name=%s ident=%s daemon=%s alive=%s",
            thread.name,
            thread.ident,
            thread.daemon,
            thread.is_alive(),
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
