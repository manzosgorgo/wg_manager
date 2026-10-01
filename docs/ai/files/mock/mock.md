# `mock/mock`

## Metadata

- Path: `mock/mock`
- Language: `unknown`
- Lines: 596
- SHA256: `88301cb28b5a3571047b57f302c09abbdda3e677f450b1529b0094b42b627ef2`

## Source

```
#!/usr/bin/env python3

import base64
import os
import sys
import tempfile
import time
from datetime import datetime, timezone


# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------

STATE_FILE = os.environ.get(
    "WG_MOCK_STATE",
    "/tmp/wg-manager-mock-state.txt"
)

LOG_FILE = os.environ.get(
    "WG_MOCK_LOG",
    "/tmp/wg-manager-mock.log"
)


# ----------------------------------------------------------------------
# WireGuard mock configuration
# ----------------------------------------------------------------------

INTERFACE_PRIVATE_KEY = (
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
)

LISTEN_PORT = "51820"
FWMARK = "off"


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

def log(message):
    """
    Append a verbose diagnostic message to the mock log.
    """

    directory = os.path.dirname(LOG_FILE)

    if directory:
        os.makedirs(directory, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()

    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {message}\n")


def log_state(peers):
    """
    Dump the complete current mock state to the log.
    """

    log(f"STATE: {len(peers)} peer(s)")

    for public_key, peer in peers.items():
        log(
            "STATE: "
            f"peer={public_key} "
            f"allowed_ips={peer['allowed_ips']} "
            f"endpoint={peer['endpoint']} "
            f"handshake={peer['handshake']} "
            f"rx={peer['rx']} "
            f"tx={peer['tx']}"
        )


# ----------------------------------------------------------------------
# State handling
# ----------------------------------------------------------------------

def load_state():
    peers = {}

    log(f"LOAD STATE: {STATE_FILE}")

    if not os.path.exists(STATE_FILE):
        log("LOAD STATE: file does not exist -> empty state")
        return peers

    with open(STATE_FILE, "r") as f:
        for line_number, line in enumerate(f, 1):

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")

            if len(fields) != 6:
                log(
                    "LOAD STATE: ignoring malformed line "
                    f"{line_number}: {line!r}"
                )
                continue

            public_key = fields[0]

            peers[public_key] = {
                "allowed_ips": fields[1],
                "endpoint": fields[2],
                "handshake": fields[3],
                "rx": fields[4],
                "tx": fields[5],
            }

    log_state(peers)

    return peers


def save_state(peers):
    directory = os.path.dirname(STATE_FILE)

    if directory:
        os.makedirs(directory, exist_ok=True)

    log(f"SAVE STATE: {STATE_FILE}")
    log_state(peers)

    fd, tmp = tempfile.mkstemp(
        dir=directory or ".",
        prefix=".mock-state-"
    )

    log(f"SAVE STATE: temporary file {tmp}")

    try:
        with os.fdopen(fd, "w") as f:

            for public_key, peer in peers.items():

                f.write(
                    "\t".join([
                        public_key,
                        peer["allowed_ips"],
                        peer["endpoint"],
                        peer["handshake"],
                        peer["rx"],
                        peer["tx"],
                    ])
                    + "\n"
                )

            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp, STATE_FILE)

        log("SAVE STATE: completed successfully")

    except Exception as exc:

        log(
            "SAVE STATE: FAILED: "
            f"{type(exc).__name__}: {exc}"
        )

        try:
            os.unlink(tmp)
        except OSError:
            pass

        raise


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------

# noinspection broad-exception
def valid_key(key):
    try:
        data = base64.b64decode(
            key,
            validate=True
        )
    except Exception as exc:
        log(
            "VALIDATE KEY: invalid base64: "
            f"{key!r}: {type(exc).__name__}: {exc}"
        )
        return False

    valid = len(data) == 32

    log(
        f"VALIDATE KEY: {key!r} -> "
        f"{'valid' if valid else 'invalid'}"
    )

    return valid


# ----------------------------------------------------------------------
# wg show
# ----------------------------------------------------------------------

def show(interface):

    log(f"SHOW: interface={interface!r}")

    if interface != "wg0":

        log(
            f"SHOW: unknown interface {interface!r}"
        )

        print(
            f"mock: unknown interface {interface}",
            file=sys.stderr
        )

        return 1

    peers = load_state()

    log(
        f"SHOW: returning interface state "
        f"with {len(peers)} peer(s)"
    )

    print(
        f"{INTERFACE_PRIVATE_KEY}\t"
        f"{LISTEN_PORT}\t"
        f"{FWMARK}"
    )

    for public_key, peer in peers.items():

        log(
            "SHOW: peer "
            f"{public_key} "
            f"allowed_ips={peer['allowed_ips']}"
        )

        print(
            "\t".join([
                public_key,
                "preshared-key",
                peer["endpoint"],
                peer["allowed_ips"],
                peer["handshake"],
                peer["rx"],
                peer["tx"],
                "0",
            ])
        )

    return 0


# ----------------------------------------------------------------------
# wg set
# ----------------------------------------------------------------------

def set_peer(args):

    log(f"SET: args={args!r}")

    if len(args) < 3:

        log("SET: invalid set command")

        print(
            "mock: invalid set command",
            file=sys.stderr
        )

        return 1

    interface = args[0]

    log(f"SET: interface={interface!r}")

    if interface != "wg0":

        log(
            f"SET: unknown interface {interface!r}"
        )

        print(
            f"mock: unknown interface {interface}",
            file=sys.stderr
        )

        return 1

    if args[1] != "peer":

        log(
            f"SET: expected 'peer', got {args[1]!r}"
        )

        print(
            "mock: expected 'peer'",
            file=sys.stderr
        )

        return 1

    public_key = args[2]

    log(
        f"SET: public_key={public_key!r}"
    )

    if not valid_key(public_key):

        log("SET: invalid public key")

        print(
            "mock: invalid public key",
            file=sys.stderr
        )

        return 1

    peers = load_state()

    # --------------------------------------------------------------
    # remove
    # --------------------------------------------------------------

    if len(args) == 4 and args[3] == "remove":

        log(
            f"SET REMOVE: peer={public_key}"
        )

        if public_key not in peers:

            log(
                "SET REMOVE: peer not found"
            )

            print(
                "mock: peer not found",
                file=sys.stderr
            )

            return 1

        del peers[public_key]

        log(
            f"SET REMOVE: peer={public_key} removed"
        )

        save_state(peers)

        return 0

    # --------------------------------------------------------------
    # allowed-ips
    # --------------------------------------------------------------

    if len(args) == 5 and args[3] == "allowed-ips":

        allowed_ips = args[4]

        log(
            "SET ALLOWED-IPS: "
            f"peer={public_key} "
            f"allowed_ips={allowed_ips!r}"
        )

        old_peer = peers.get(public_key)

        if old_peer is None:
            log(
                "SET ALLOWED-IPS: creating new peer"
            )
        else:
            log(
                "SET ALLOWED-IPS: updating existing peer "
                f"old_allowed_ips={old_peer['allowed_ips']!r}"
            )

        peers[public_key] = {
            "allowed_ips": allowed_ips,
            "endpoint": "(none)",
            "handshake": "0",
            "rx": "0",
            "tx": "0",
        }

        save_state(peers)

        return 0

    # --------------------------------------------------------------
    # unsupported
    # --------------------------------------------------------------

    log(
        f"SET: unsupported command: {args!r}"
    )

    print(
        "mock: unsupported set command",
        file=sys.stderr
    )

    return 1


# ----------------------------------------------------------------------
# handshake (mock only, not a real wg command)
# ----------------------------------------------------------------------

def handshake(args):
    """
    Simulate a completed handshake of an existing peer:

        mock handshake <interface> <public_key> [endpoint]

    Sets latest_handshake to now and gives the peer an endpoint
    and some traffic, so "wg show dump" reports it as paired.
    """

    log(f"HANDSHAKE: args={args!r}")

    if len(args) not in (2, 3):

        log("HANDSHAKE: invalid handshake command")

        print(
            "mock: usage: handshake <interface> <public_key> [endpoint]",
            file=sys.stderr
        )

        return 1

    interface, public_key = args[0], args[1]
    endpoint = args[2] if len(args) == 3 else "192.0.2.10:51820"

    if interface != "wg0":

        log(
            f"HANDSHAKE: unknown interface {interface!r}"
        )

        print(
            f"mock: unknown interface {interface}",
            file=sys.stderr
        )

        return 1

    peers = load_state()

    peer = peers.get(public_key)

    if peer is None:

        log("HANDSHAKE: peer not found")

        print(
            "mock: peer not found",
            file=sys.stderr
        )

        return 1

    peer["endpoint"] = endpoint
    peer["handshake"] = str(int(time.time()))
    peer["rx"] = str(int(peer["rx"]) + 1024)
    peer["tx"] = str(int(peer["tx"]) + 1024)

    log(
        "HANDSHAKE: "
        f"peer={public_key} "
        f"endpoint={endpoint} "
        f"handshake={peer['handshake']}"
    )

    save_state(peers)

    return 0


# ----------------------------------------------------------------------
# Main command dispatcher
# ----------------------------------------------------------------------

def main():

    log("=" * 72)
    log(
        "START: "
        f"argv={sys.argv!r} "
        f"pid={os.getpid()}"
    )
    log(
        f"START: state_file={STATE_FILE}"
    )
    log(
        f"START: log_file={LOG_FILE}"
    )

    if len(sys.argv) < 2:

        log("MAIN: missing command")

        print(
            "mock: missing command",
            file=sys.stderr
        )

        return 1

    command = sys.argv[1:]

    log(f"MAIN: command={command!r}")

    # --------------------------------------------------------------
    # wg show <interface> dump
    # --------------------------------------------------------------

    if (
        len(command) == 3
        and command[0] == "show"
        and command[2] == "dump"
    ):

        result = show(command[1])

        log(
            f"MAIN: show returned {result}"
        )

        return result

    # --------------------------------------------------------------
    # wg set ...
    # --------------------------------------------------------------

    if command[0] == "set":

        result = set_peer(command[1:])

        log(
            f"MAIN: set returned {result}"
        )

        return result

    # --------------------------------------------------------------
    # handshake <interface> <public_key> [endpoint]
    # --------------------------------------------------------------

    if command[0] == "handshake":

        result = handshake(command[1:])

        log(
            f"MAIN: handshake returned {result}"
        )

        return result

    # --------------------------------------------------------------
    # unsupported command
    # --------------------------------------------------------------

    log(
        f"MAIN: unsupported command: {command!r}"
    )

    print(
        "mock: unsupported command:",
        *command,
        file=sys.stderr
    )

    return 1


if __name__ == "__main__":
    result = main()

    log(f"EXIT: {result}")
    log("=" * 72)

    sys.exit(result)
```
