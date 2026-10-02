#!/usr/bin/env python3

import argparse
import getpass
import sys
from pathlib import Path

# Allow direct execution as "python3 tools/manage_users.py" from any cwd.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import opaque

from src.wg_auth.wg_auth_user_store import WGAuthUserStore
from src.wg_auth.wg_auth_peer_registry import WGAuthPeerRegistry
from src.wg_auth.wg_auth_ownership_service import WGAuthOwnershipService
from src.wg_auth.wg_auth_account_service import WGAuthAccountService


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

    claim = sub.add_parser("claim-peer")
    claim.add_argument("username")
    claim.add_argument("public_key")

    parser.add_argument(
        "--peer-registry",
        default=None,
        help="peer registry path (defaults to <login-dir>/.peer_registry.json)",
    )

    args = parser.parse_args()

    store = WGAuthUserStore(
        args.login_dir,
        opaque_record_len=opaque.OPAQUE_USER_RECORD_LEN,
    )

    registry = WGAuthPeerRegistry(
        args.peer_registry
        or str(Path(args.login_dir) / ".peer_registry.json")
    )
    ownership = WGAuthOwnershipService(
        store,
        registry,
    )
    accounts = WGAuthAccountService(
        store,
    )

    try:
        if args.command == "create":
            if args.password_stdin:
                password = sys.stdin.readline().rstrip("\n")
            else:
                password = read_password_from_tty()

            accounts.create(
                args.username,
                password,
            )
            print(f"created user '{args.username}'")
            return 0

        if args.command == "delete":
            accounts.delete(args.username)
            print(f"deleted user '{args.username}'")
            return 0

        result = ownership.reassign(
            args.public_key,
            args.username,
        )
        print(
            f"peer '{result['public_key']}' assigned to "
            f"'{result['owner']}'"
        )
        return 0

    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
