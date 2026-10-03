#!/usr/bin/env python3

"""
Load and validate wg-client runtime configuration.

WG_CLIENT_CONFIG selects the INI file. The loader normalizes numeric values,
applies secure-session defaults and rejects invalid port, timeout, counter,
replay-window and request-rate combinations before runtime starts.
"""

import configparser
import math
import os


DEFAULT_CONFIG = "/home/main/Desktop/wg_manager/config/wg-client-test-auth.conf"

# Secure Session defaults
DEFAULT_SECURE_SESSION_ENABLED = True
DEFAULT_SESSION_ID_SIZE = 16
DEFAULT_NONCE_SIZE = 32
DEFAULT_SESSION_KEY_SIZE = 32
DEFAULT_COUNTER_MIN = 1
DEFAULT_COUNTER_MAX = 0xFFFFFFFF
DEFAULT_SESSION_TIMEOUT = 86400
# Zero disables runtime frequency enforcement. When enabled, this value is
# requests per second and is checked against the session counter capacity.
DEFAULT_MAX_REQUEST_FREQUENCY = 0.0
DEFAULT_REPLAY_WINDOW_SIZE = 64


def load_config():
    """
    Load, validate and normalize the selected wg-client INI configuration.
    """
    path = os.environ.get(
        "WG_CLIENT_CONFIG",
        DEFAULT_CONFIG,
    )

    config = configparser.ConfigParser()

    if not config.read(path):
        raise RuntimeError(f"cannot read configuration file: {path}")

    required = (
        ("api", "host"),
        ("api", "port"),
        ("api", "server_cert"),
        ("api", "server_key"),
        ("api", "ca"),
        ("controller", "host"),
        ("controller", "port"),
        ("controller", "ca"),
        ("controller", "client_cert"),
        ("controller", "client_key"),
        ("controller", "timeout"),
        ("wireguard", "interface"),
    )

    for section, option in required:
        if not config.has_option(section, option):
            raise RuntimeError(
                f"missing configuration option [{section}] {option}"
            )

    # API configuration
    api_port = config.getint("api", "port")

    if api_port not in range(1, 65536):
        raise RuntimeError("invalid API port")

    # Controller configuration
    controller_port = config.getint("controller", "port")

    if controller_port not in range(1, 65536):
        raise RuntimeError("invalid controller port")

    controller_timeout = config.getint("controller", "timeout")

    if controller_timeout <= 0:
        raise RuntimeError("invalid controller timeout")

    wireguard_endpoint = config.get(
        "wireguard",
        "endpoint",
        fallback="",
    ).strip()

    # Secure Session configuration.
    # The whole section is optional; defaults are used when absent.
    secure_session_enabled = config.getboolean(
        "secure_session",
        "enabled",
        fallback=DEFAULT_SECURE_SESSION_ENABLED,
    )

    session_id_size = config.getint(
        "secure_session",
        "session_id_size",
        fallback=DEFAULT_SESSION_ID_SIZE,
    )

    nonce_size = config.getint(
        "secure_session",
        "nonce_size",
        fallback=DEFAULT_NONCE_SIZE,
    )

    session_key_size = config.getint(
        "secure_session",
        "session_key_size",
        fallback=DEFAULT_SESSION_KEY_SIZE,
    )

    counter_min = config.getint(
        "secure_session",
        "counter_min",
        fallback=DEFAULT_COUNTER_MIN,
    )

    counter_max = config.getint(
        "secure_session",
        "counter_max",
        fallback=DEFAULT_COUNTER_MAX,
    )

    session_timeout = config.getint(
        "secure_session",
        "session_timeout",
        fallback=DEFAULT_SESSION_TIMEOUT,
    )

    max_request_frequency = config.getfloat(
        "secure_session",
        "max_request_frequency",
        fallback=DEFAULT_MAX_REQUEST_FREQUENCY,
    )

    replay_window_size = config.getint(
        "secure_session",
        "replay_window_size",
        fallback=DEFAULT_REPLAY_WINDOW_SIZE,
    )

    if session_id_size <= 0:
        raise RuntimeError("invalid secure session ID size")

    if nonce_size <= 0:
        raise RuntimeError("invalid secure session nonce size")

    if session_key_size <= 0:
        raise RuntimeError("invalid secure session key size")

    if counter_min < 1:
        raise RuntimeError("invalid secure session counter minimum")

    if counter_max < counter_min:
        raise RuntimeError("invalid secure session counter range")

    if session_timeout <= 0:
        raise RuntimeError("invalid secure session timeout")

    if (
        not math.isfinite(max_request_frequency)
        or max_request_frequency < 0
    ):
        raise RuntimeError("invalid secure session maximum request frequency")

    if replay_window_size <= 0:
        raise RuntimeError("invalid secure session replay window size")

    counter_capacity = counter_max - counter_min + 1
    if (
        max_request_frequency > 0
        and max_request_frequency * session_timeout > counter_capacity
    ):
        raise RuntimeError(
            "secure session request frequency and timeout exceed "
            "counter capacity"
        )

    return {
        "api": {
            "host": config["api"]["host"].strip(),
            "port": api_port,
            "server_cert": config["api"]["server_cert"].strip(),
            "server_key": config["api"]["server_key"].strip(),
            "ca": config["api"]["ca"].strip(),
        },
        "controller": {
            "host": config["controller"]["host"].strip(),
            "port": controller_port,
            "ca": config["controller"]["ca"].strip(),
            "client_cert": config["controller"]["client_cert"].strip(),
            "client_key": config["controller"]["client_key"].strip(),
            "timeout": controller_timeout,
        },
        "wireguard": {
            "interface": config["wireguard"]["interface"].strip(),
            "endpoint": wireguard_endpoint or None,
        },
        "secure_session": {
            "enabled": secure_session_enabled,
            "session_id_size": session_id_size,
            "nonce_size": nonce_size,
            "session_key_size": session_key_size,
            "counter_min": counter_min,
            "counter_max": counter_max,
            "session_timeout": session_timeout,
            "max_request_frequency": max_request_frequency,
            "replay_window_size": replay_window_size,
        },
    }