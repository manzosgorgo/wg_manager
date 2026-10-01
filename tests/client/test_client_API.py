#!/usr/bin/env python3

import logging
import os
import threading
import time

from src.wg_client.wg_client_API import WGClientAPI
from src.wg_client.wg_client_config import load_config


LISTEN_PATH = ""


def main():

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s"
    )

    os.environ.setdefault("WG_CLIENT_CONFIG", "config/wg-client-test.conf")

    cfg = load_config()

    print("=== WGClientAPI HTTPS test ===")

    api = WGClientAPI(cfg, LISTEN_PATH)

    print("\n--- Starting server ---")

    api.bind()

    server_thread = threading.Thread(
        target=api.serve,
        daemon=True
    )

    server_thread.start()

    time.sleep(1)

    print("\n--- Server started ---")
    print(
        f"HTTPS server listening on "
        f"https://{api.host}:{api.port}{LISTEN_PATH}/v1/status"
    )

    print("\nPress ENTER to stop the server.")

    input()

    print("\n--- Stopping server ---")

    api.stop()

    server_thread.join()

    print("\n=== TEST FINISHED ===")


if __name__ == "__main__":
    main()
