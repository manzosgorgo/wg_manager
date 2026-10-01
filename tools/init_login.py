#!/usr/bin/env python3

import base64
import getpass
import json
import os
import sys

import opaque


USERNAME = "admin"
LOGIN_DIR = "login"
CONTEXT = b"wg-manager"


def main():
    path = os.path.join(LOGIN_DIR, USERNAME)

    if not os.path.isdir(LOGIN_DIR):
        print(f"error: directory '{LOGIN_DIR}' does not exist", file=sys.stderr)
        return 1

    if os.path.exists(path):
        print(f"error: login record already exists: '{path}'", file=sys.stderr)
        return 1

    password = getpass.getpass("Master password: ")
    password_confirm = getpass.getpass("Confirm master password: ")

    if not password:
        print("error: password cannot be empty", file=sys.stderr)
        return 1

    if password != password_confirm:
        print("error: passwords do not match", file=sys.stderr)
        return 1

    password = password.encode()

    ids = opaque.Ids(
        USERNAME.encode(),
        b"wg-auth",
    )

    # OPAQUE registration
    secU, M = opaque.CreateRegistrationRequest(password)

    secS, pub = opaque.CreateRegistrationResponse(M)

    rec0, _export_key = opaque.FinalizeRequest(
        secU,
        pub,
        ids,
    )

    record = opaque.StoreUserRecord(
        secS,
        rec0,
    )

    if len(record) != opaque.OPAQUE_USER_RECORD_LEN:
        print(
            f"error: unexpected record size: {len(record)}",
            file=sys.stderr,
        )
        return 1

    user_record = {
        "opaque_record": base64.b64encode(record).decode("ascii"),
        "peers": [],
    }

    with open(path, "x", encoding="utf-8") as f:
        json.dump(user_record, f, indent=2)
        f.write("\n")

    os.chmod(path, 0o600)

    print(f"created user record for '{USERNAME}'")
    print(f"path: {path}")
    print(f"OPAQUE record size: {len(record)} bytes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
