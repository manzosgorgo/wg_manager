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