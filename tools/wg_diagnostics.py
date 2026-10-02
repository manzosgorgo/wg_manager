#!/usr/bin/env python3
"""Read-only diagnostic snapshot for wg_manager."""

from __future__ import annotations

import argparse
import configparser
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"

UNITS = (
    "wg-client-test.socket",
    "wg-client-test@.service",
    "wg-controller-test.socket",
    "wg-controller-test@.service",
)

ENV_KEYS = (
    "WG_CLIENT_CONFIG",
    "WG_CONFIG",
    "WG_PROGRAM",
    "WG_MOCK_STATE",
    "WG_MOCK_LOG",
    "PYTHONPATH",
)

PATH_KEYS = {
    "login_dir",
    "peer_registry",
    "socket_path",
    "server_cert",
    "server_key",
    "ca",
    "ca_cert",
    "client_cert",
    "client_key",
}


def run(cmd, timeout=8):
    try:
        p = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return p.returncode, p.stdout, p.stderr
    except Exception as exc:
        return 1, "", f"{type(exc).__name__}: {exc}"


def heading(text):
    print("\n" + "=" * 78)
    print(text)
    print("=" * 78)


def subheading(text):
    print(f"\n--- {text} ---")


def file_info(path):
    p = Path(path)
    try:
        st = p.stat()
    except OSError as exc:
        return f"MISSING ({type(exc).__name__}: {exc})"

    kind = (
        "dir" if p.is_dir()
        else "socket" if p.is_socket()
        else "file" if p.is_file()
        else "other"
    )
    return (
        f"{kind} size={st.st_size} "
        f"mode={oct(st.st_mode & 0o7777)} uid={st.st_uid} gid={st.st_gid}"
    )


def parse_env(text):
    result = {}
    try:
        fields = shlex.split(text)
    except ValueError:
        fields = text.split()

    for field in fields:
        if "=" in field:
            key, value = field.split("=", 1)
            result[key] = value
    return result


def unit_report():
    heading("SYSTEMD / RUNTIME SELECTION")
    selected = {}

    for unit in UNITS:
        subheading(unit)
        rc, out, err = run([
            "systemctl", "show", unit,
            "--property=LoadState,ActiveState,SubState,UnitFileState,"
            "FragmentPath,Environment,ExecStart",
            "--no-pager",
        ])

        if rc:
            print(err.strip() or "unavailable")
            continue

        data = {}
        for line in out.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key] = value

        for key in (
            "LoadState",
            "ActiveState",
            "SubState",
            "UnitFileState",
            "FragmentPath",
            "ExecStart",
        ):
            if data.get(key):
                print(f"{key}: {data[key]}")

        env = parse_env(data.get("Environment", ""))
        if env:
            print("Environment:")
            for key, value in sorted(env.items()):
                print(f"  {key}={value}")
                if key in ENV_KEYS:
                    selected[key] = value

    return selected


def read_ini(path):
    cfg = configparser.ConfigParser()
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg.read_file(f)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return cfg, None


def config_report(selected):
    heading("CONFIGURATION")

    selected_paths = {
        str(Path(p).resolve())
        for p in (
            selected.get("WG_CLIENT_CONFIG"),
            selected.get("WG_CONFIG"),
            str(CONFIG_DIR / "wg-auth.conf"),
        )
        if p
    }

    for path in sorted(CONFIG_DIR.glob("*.conf")):
        mark = " [SELECTED]" if str(path.resolve()) in selected_paths else ""
        subheading(str(path) + mark)

        cfg, err = read_ini(path)
        if cfg is None:
            print(err)
            continue

        for section in cfg.sections():
            print(f"[{section}]")
            for key, value in cfg.items(section):
                print(f"  {key} = {value}")

        refs = []
        for section in cfg.sections():
            for key, value in cfg.items(section):
                if key in PATH_KEYS and value.startswith("/"):
                    refs.append((section, key, value))

        if refs:
            print("Referenced files:")
            for section, key, value in refs:
                print(
                    f"  [{section}] {key}: {value} "
                    f"[{file_info(value)}]"
                )


def auth_report():
    heading("AUTH / OWNERSHIP")

    cfg, err = read_ini(CONFIG_DIR / "wg-auth.conf")
    if cfg is None:
        print(err)
        return

    login_dir = Path(cfg["auth"]["login_dir"])
    registry = Path(
        cfg["auth"].get(
            "peer_registry",
            str(login_dir / ".peer_registry.json"),
        )
    )

    print(f"login_dir: {login_dir} [{file_info(login_dir)}]")
    print(f"registry: {registry} [{file_info(registry)}]")

    subheading("users")
    if login_dir.is_dir():
        for path in sorted(login_dir.iterdir()):
            if path.name.startswith(".") or not path.is_file():
                continue
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
                peers = obj.get("peers")
                print(
                    f"{path.name}: peers="
                    f"{len(peers) if isinstance(peers, list) else 'INVALID'}; "
                    f"opaque_record="
                    f"{'present' if isinstance(obj.get('opaque_record'), str) else 'INVALID'}"
                )
                if isinstance(peers, list):
                    for peer in peers:
                        print(f"  {peer}")
            except Exception as exc:
                print(f"{path.name}: INVALID {type(exc).__name__}: {exc}")

    subheading("peer registry")
    if registry.exists():
        try:
            obj = json.loads(registry.read_text(encoding="utf-8"))
            peers = obj.get("peers", {})
            print(f"entries: {len(peers) if isinstance(peers, dict) else 'INVALID'}")
            if isinstance(peers, dict):
                for key, entry in sorted(peers.items()):
                    print(
                        f"{key}: ip={entry.get('allowed_ip')} "
                        f"owner={entry.get('username')} "
                        f"state={entry.get('ownership_state')}"
                    )
        except Exception as exc:
            print(f"INVALID: {type(exc).__name__}: {exc}")


def mock_report(selected):
    heading("MANAGER / MOCK")

    for key in ("WG_PROGRAM", "WG_MOCK_STATE", "WG_MOCK_LOG"):
        value = selected.get(key)
        print(f"{key}: {value or '(not selected by installed unit)'}")
        if value and key != "WG_PROGRAM":
            print(f"  {file_info(value)}")

    state = selected.get("WG_MOCK_STATE")
    if state and Path(state).exists():
        subheading("mock peers")
        for n, line in enumerate(
            Path(state).read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines(),
            1,
        ):
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) != 6:
                print(f"line {n}: INVALID {line!r}")
                continue
            print(
                f"key={fields[0]} ip={fields[1]} endpoint={fields[2]} "
                f"handshake={fields[3]} rx={fields[4]} tx={fields[5]}"
            )


def socket_report():
    heading("KNOWN SOCKETS / LISTENERS")

    unix_path = "/run/wg_manager/wg-client-test.sock"
    print(f"{unix_path}: {file_info(unix_path)}")

    rc, out, err = run(["ss", "-ltnx"])
    if rc:
        print(err.strip() or "ss unavailable")
        return

    wanted = ("9443", "9444", "9445", "wg-client-test.sock")
    for line in out.splitlines():
        if any(item in line for item in wanted):
            print(line)


def logs_report(selected, lines):
    heading(f"LOGS / LAST {lines} LINES")

    mock_log = selected.get("WG_MOCK_LOG")
    if mock_log:
        subheading(f"mock: {mock_log}")
        p = Path(mock_log)
        if p.exists():
            content = p.read_text(
                encoding="utf-8",
                errors="replace",
            ).splitlines()
            for line in content[-lines:]:
                print(line)
        else:
            print("(missing)")

    for unit in UNITS:
        subheading(f"journal: {unit}")
        rc, out, err = run([
            "journalctl", "-u", unit,
            "-n", str(lines),
            "--no-pager", "-o", "short-iso",
        ])
        print(out.rstrip() if rc == 0 and out.strip() else err.strip() or "(no entries)")


def source_fallbacks():
    heading("SOURCE FALLBACKS")
    print(
        "client default config: "
        "/home/main/Desktop/wg_manager/config/wg-client-test-auth.conf"
    )
    print(
        "auth config path: "
        "/home/main/Desktop/wg_manager/config/wg-auth.conf"
    )
    print("mock default state: /tmp/wg-manager-mock-state.txt")
    print("mock default log: /tmp/wg-manager-mock.log")


def main():
    parser = argparse.ArgumentParser(
        description="Print a read-only wg_manager diagnostic snapshot."
    )
    parser.add_argument(
        "--journal-lines",
        type=int,
        default=30,
    )
    parser.add_argument(
        "--no-logs",
        action="store_true",
    )
    args = parser.parse_args()

    print("wg_manager diagnostic snapshot")
    print(f"repository: {ROOT}")
    print(f"python: {sys.executable}")
    print(f"uid: {os.getuid()}")

    selected = unit_report()
    config_report(selected)
    source_fallbacks()
    auth_report()
    mock_report(selected)
    socket_report()

    if not args.no_logs:
        logs_report(selected, max(args.journal_lines, 1))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
