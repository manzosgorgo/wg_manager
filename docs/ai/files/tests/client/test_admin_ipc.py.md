# `tests/client/test_admin_ipc.py`

## Metadata

- Path: `tests/client/test_admin_ipc.py`
- Language: `python`
- Lines: 179
- SHA256: `cf9888a267e0549240de09eafb474e98000de55e78c936226b7d78631f9dd2f2`
- Imports:
  - `socket`
  - `src.wg_auth.wg_auth_IPC`
  - `src.wg_client.wg_client_IPC`
  - `src.wg_client.wg_client_errors`
  - `threading`

## Source

```python
#!/usr/bin/env python3

import socket
import threading

from src.wg_auth.wg_auth_IPC import WGAuthIPC
from src.wg_client.wg_client_IPC import WGClientIPC


class AuthLifecycle:
    def __init__(self):
        self.shutdown_calls = []

    def request_session_shutdown(self, notify_client=True):
        self.shutdown_calls.append(notify_client)

    def request_shutdown(self):
        self.shutdown_calls.append("shutdown")


class ClientLifecycle:
    pass


def test_admin_ipc_round_trip_for_ownership_and_accounts():
    auth_sock, client_sock = socket.socketpair()

    calls = []
    auth_lifecycle = AuthLifecycle()

    auth = WGAuthIPC(
        socket_path="unused",
        client_id="test",
        timeout=30,
        listen_path="/api/test",
        lifecycle=auth_lifecycle,
        principal={"username": "admin", "peers": []},
        ownership_state=lambda: {
            "users": ["admin", "alice"],
            "peers": [],
            "ips": {},
        },
        ownership_reassign=lambda public_key, username: calls.append(
            ("reassign", public_key, username)
        ) or {
            "public_key": public_key,
            "owner": username,
        },
        account_create=lambda username, password: calls.append(
            ("create", username, password)
        ) or {
            "username": username,
            "peers": [],
        },
        account_delete=lambda username: calls.append(
            ("delete", username)
        ) or {
            "username": username,
            "deleted": True,
        },
    )
    auth.sock = auth_sock

    client = WGClientIPC(client_sock, ClientLifecycle())

    auth_thread = threading.Thread(
        target=auth.control_loop,
        daemon=True,
    )
    client_thread = threading.Thread(
        target=client.control_loop,
        daemon=True,
    )

    auth_thread.start()
    client_thread.start()

    try:
        state = client.ownership_state()
        assert state == {
            "users": ["admin", "alice"],
            "peers": [],
            "ips": {},
        }

        reassigned = client.reassign_owner(
            "peer-a",
            "alice",
        )
        assert reassigned == {
            "public_key": "peer-a",
            "owner": "alice",
        }

        created = client.create_user(
            "bob",
            "secret-password",
        )
        assert created == {
            "username": "bob",
            "peers": [],
        }

        deleted = client.delete_user("bob")
        assert deleted == {
            "username": "bob",
            "deleted": True,
        }

        assert calls == [
            ("reassign", "peer-a", "alice"),
            ("create", "bob", "secret-password"),
            ("delete", "bob"),
        ]

        client.stop(notify_shutdown=True)

        auth_thread.join(timeout=2)
        client_thread.join(timeout=2)

        assert not auth_thread.is_alive()
        assert not client_thread.is_alive()

    finally:
        auth.close()
        client.stop(notify_shutdown=False)
        auth_sock.close()
        client_sock.close()


def test_non_admin_account_ipc_is_rejected_with_403():
    auth_sock, client_sock = socket.socketpair()

    auth = WGAuthIPC(
        socket_path="unused",
        client_id="test",
        timeout=30,
        listen_path="/api/test",
        lifecycle=AuthLifecycle(),
        principal={"username": "alice", "peers": []},
        account_create=lambda username, password: {
            "username": username,
            "peers": [],
        },
    )
    auth.sock = auth_sock

    client = WGClientIPC(client_sock, ClientLifecycle())

    auth_thread = threading.Thread(
        target=auth.control_loop,
        daemon=True,
    )
    client_thread = threading.Thread(
        target=client.control_loop,
        daemon=True,
    )
    auth_thread.start()
    client_thread.start()

    try:
        from src.wg_client.wg_client_errors import WGPeerPersistenceError

        try:
            client.create_user("bob", "secret")
        except WGPeerPersistenceError as exc:
            assert exc.status == 403
        else:
            raise AssertionError("non-admin account create unexpectedly succeeded")

        client.stop(notify_shutdown=True)

    finally:
        auth_thread.join(timeout=2)
        client_thread.join(timeout=2)
        auth.close()
        client.stop(notify_shutdown=False)
        auth_sock.close()
        client_sock.close()
```
