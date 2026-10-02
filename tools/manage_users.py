#!/usr/bin/env python3

import argparse
import getpass
import sys

import opaque

from src.wg_auth.wg_auth_user_store import WGAuthUserStore


SERVER_ID = b"wg-auth"


def make_opaque_record(username, password):
    if not password:
        raise ValueError("password cannot be empty")

    ids = opaque.Ids(
        username.encode("utf-8"),
        SERVER_ID,
    )

    sec_u, request = opaque.CreateRegistrationRequest(
        password.encode("utf-8")
    )
    sec_s, response = opaque.CreateRegistrationResponse(request)
    rec0, _export_key = opaque.FinalizeRequest(
        sec_u,
        response,
        ids,
    )
    record = opaque.StoreUserRecord(sec_s, rec0)

    if len(record) != opaque.OPAQUE_USER_RECORD_LEN:
        raise RuntimeError(
            f"unexpected OPAQUE record size: {len(record)}"
        )

    return record


def read_password_from_tty():
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        raise ValueError("passwords do not match")

    return password


def main():
    parser = argparse.ArgumentParser(
        description="Manage wg-auth local user records."
    )
    parser.add_argument(
        "--login-dir",
        default="login",
        help="directory containing wg-auth user records",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("username")
    create.add_argument(
        "--password-stdin",
        action="store_true",
        help="read one password line from stdin",
    )

    delete = sub.add_parser("delete")
    delete.add_argument("username")

    args = parser.parse_args()

    store = WGAuthUserStore(
        args.login_dir,
        opaque_record_len=opaque.OPAQUE_USER_RECORD_LEN,
    )

    try:
        if args.command == "create":
            if args.password_stdin:
                password = sys.stdin.readline().rstrip("\n")
            else:
                password = read_password_from_tty()

            record = make_opaque_record(
                args.username,
                password,
            )
            store.create_user(
                args.username,
                record,
            )
            print(f"created user '{args.username}'")
            return 0

        store.delete_user(args.username)
        print(f"deleted user '{args.username}'")
        return 0

    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
