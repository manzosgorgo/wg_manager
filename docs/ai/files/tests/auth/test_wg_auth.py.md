# `tests/auth/test_wg_auth.py`

## Metadata

- Path: `tests/auth/test_wg_auth.py`
- Language: `python`
- Lines: 496
- SHA256: `bcec95380b89f31d243bffd242add65dbd9bad1d68b6144f7d88ff0e2b078ae5`
- Imports:
  - `json`
  - `ssl`
  - `subprocess`
  - `sys`
  - `time`
  - `urllib.error`
  - `urllib.request`

## Source

```python
#!/usr/bin/env python3

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request


AUTH_URL = "https://127.0.0.1:9445"

VALID_ID = "test-user"
INVALID_ID = "definitely-invalid"

CLIENT_SERVICE_PREFIX = "wg-client-test@"

REQUEST_TIMEOUT = 3
POLL_INTERVAL = 0.2
POLL_TIMEOUT = 5


class TestFailure(Exception):
    pass


def log(message):
    print(f"[TEST] {message}")


def success(message):
    print(f"[ OK ] {message}")


def fail(message):
    print(f"[FAIL] {message}")
    raise TestFailure(message)


def request(method, path, payload=None):
    url = AUTH_URL + path

    data = None

    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request_obj = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    # Test environment: ignore the local test certificate.
    import ssl

    context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(
            request_obj,
            timeout=REQUEST_TIMEOUT,
            context=context,
        ) as response:

            body = response.read()

            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = body.decode("utf-8")

            return response.status, payload

    except urllib.error.HTTPError as exc:
        body = exc.read()

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body.decode("utf-8")

        return exc.code, payload

    except urllib.error.URLError as exc:
        fail(f"cannot contact wg-auth: {exc}")


def systemctl(*args):
    result = subprocess.run(
        ["systemctl", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return result


def client_services():
    result = systemctl(
        "list-units",
        "--all",
        "--no-legend",
        "--plain",
        f"{CLIENT_SERVICE_PREFIX}*.service",
    )

    if result.returncode != 0:
        return []

    services = []

    for line in result.stdout.splitlines():
        fields = line.split()

        if not fields:
            continue

        unit = fields[0]

        if not unit.startswith(CLIENT_SERVICE_PREFIX):
            continue

        services.append(
            {
                "unit": unit,
                "active": len(fields) > 2 and fields[2] == "active",
                "state": fields[2] if len(fields) > 2 else None,
            }
        )

    return services


def active_client_services():
    return [
        service
        for service in client_services()
        if service["active"]
    ]


def wait_for_client_service(expected, description):
    deadline = time.monotonic() + POLL_TIMEOUT

    while time.monotonic() < deadline:

        services = active_client_services()

        if expected and services:
            success(
                f"{description}: "
                + ", ".join(s["unit"] for s in services)
            )
            return services

        if not expected and not services:
            success(description)
            return []

        time.sleep(POLL_INTERVAL)

    services = active_client_services()

    if expected:
        fail(
            f"{description}: no active wg-client service found"
        )

    fail(
        f"{description}: wg-client service still active: "
        + ", ".join(s["unit"] for s in services)
    )


def expect_status(expected_http, expected_authenticated):
    status, body = request("GET", "/status")

    if status != expected_http:
        fail(
            f"GET /status returned HTTP {status}, "
            f"expected {expected_http}: {body}"
        )

    if body.get("authenticated") != expected_authenticated:
        fail(
            f"GET /status authenticated={body.get('authenticated')}, "
            f"expected {expected_authenticated}: {body}"
        )

    success(
        f"GET /status → authenticated={expected_authenticated}"
    )

    return body


def main():
    print()
    print("=" * 70)
    print("WG-AUTH INTEGRATION TEST")
    print("=" * 70)
    print()

    # ------------------------------------------------------------------
    # 0. Verify that wg-auth is reachable
    # ------------------------------------------------------------------

    log("checking that wg-auth is running")

    expect_status(
        expected_http=200,
        expected_authenticated=False,
    )

    # ------------------------------------------------------------------
    # 1. Invalid authentication
    # ------------------------------------------------------------------

    log("testing invalid authentication")

    status, body = request(
        "POST",
        "/auth",
        {
            "fake_id": INVALID_ID,
        },
    )

    if status != 401:
        fail(
            f"invalid authentication returned HTTP {status}, "
            f"expected 401: {body}"
        )

    success("invalid authentication correctly rejected")

    expect_status(
        expected_http=200,
        expected_authenticated=False,
    )

    wait_for_client_service(
        expected=False,
        description="no client service after failed authentication",
    )

    # ------------------------------------------------------------------
    # 2. Valid authentication
    # ------------------------------------------------------------------

    log("testing valid authentication")

    status, body = request(
        "POST",
        "/auth",
        {
            "fake_id": VALID_ID,
        },
    )

    if status != 200:
        fail(
            f"valid authentication returned HTTP {status}: {body}"
        )

    if not body.get("ok"):
        fail(
            f"valid authentication returned ok=false: {body}"
        )

    session_id_1 = body.get("session_id")
    k_session_1 = body.get("k_session")
    activation = body.get("activation")

    if not session_id_1:
        fail("authentication response has no session_id")

    if not k_session_1:
        fail("authentication response has no k_session")

    if not isinstance(activation, dict):
        fail("authentication response has no activation object")

    if activation.get("type") != "ACTIVATION_RESULT":
        fail(
            f"unexpected activation type: {activation}"
        )

    if activation.get("status") != "OK":
        fail(
            f"activation was not successful: {activation}"
        )

    success(
        f"authenticated successfully: session_id={session_id_1}"
    )

    # ------------------------------------------------------------------
    # 3. Verify wg-client systemd service
    # ------------------------------------------------------------------

    wait_for_client_service(
        expected=True,
        description="wg-client service started after authentication",
    )

    # ------------------------------------------------------------------
    # 4. Verify authenticated status
    # ------------------------------------------------------------------

    status_body = expect_status(
        expected_http=200,
        expected_authenticated=True,
    )

    if not status_body.get("client_active"):
        fail(
            f"/status says client_active=false after activation: "
            f"{status_body}"
        )

    success("status reports active client")

    # ------------------------------------------------------------------
    # 5. Try second authentication while session is active
    # ------------------------------------------------------------------

    log("testing authentication while a session is already active")

    status, body = request(
        "POST",
        "/auth",
        {
            "fake_id": VALID_ID,
        },
    )

    if status == 200:
        fail(
            "second authentication unexpectedly succeeded while "
            "a session was already active"
        )

    success(
        f"second authentication rejected as expected "
        f"(HTTP {status})"
    )

    # Verify that the original session is still alive.

    status_body = expect_status(
        expected_http=200,
        expected_authenticated=True,
    )

    if not status_body.get("client_active"):
        fail(
            "original client disappeared after rejected second authentication"
        )

    # ------------------------------------------------------------------
    # 6. Logout
    # ------------------------------------------------------------------

    log("testing logout")

    status, body = request(
        "DELETE",
        "/auth",
    )

    if status != 200:
        fail(
            f"DELETE /auth returned HTTP {status}: {body}"
        )

    if not body.get("ok"):
        fail(
            f"DELETE /auth returned ok=false: {body}"
        )

    success("logout request accepted")

    # ------------------------------------------------------------------
    # 7. Verify session really disappeared
    # ------------------------------------------------------------------

    expect_status(
        expected_http=200,
        expected_authenticated=False,
    )

    wait_for_client_service(
        expected=False,
        description="wg-client service stopped after logout",
    )

    # ------------------------------------------------------------------
    # 8. Authenticate again
    # ------------------------------------------------------------------

    log("testing second complete authentication cycle")

    status, body = request(
        "POST",
        "/auth",
        {
            "fake_id": VALID_ID,
        },
    )

    if status != 200:
        fail(
            f"second authentication returned HTTP {status}: {body}"
        )

    if not body.get("ok"):
        fail(
            f"second authentication returned ok=false: {body}"
        )

    session_id_2 = body.get("session_id")

    if not session_id_2:
        fail("second authentication has no session_id")

    if session_id_2 == session_id_1:
        fail(
            "second authentication reused the previous session_id"
        )

    success(
        f"second authentication successful: session_id={session_id_2}"
    )

    wait_for_client_service(
        expected=True,
        description="wg-client service started for second session",
    )

    expect_status(
        expected_http=200,
        expected_authenticated=True,
    )

    # ------------------------------------------------------------------
    # 9. Final logout
    # ------------------------------------------------------------------

    log("final logout")

    status, body = request(
        "DELETE",
        "/auth",
    )

    if status != 200:
        fail(
            f"final DELETE /auth returned HTTP {status}: {body}"
        )

    expect_status(
        expected_http=200,
        expected_authenticated=False,
    )

    wait_for_client_service(
        expected=False,
        description="final wg-client service shutdown",
    )

    print()
    print("=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)
    print()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TestFailure:
        print()
        print("=" * 70)
        print("TEST FAILED")
        print("=" * 70)
        print()
        raise SystemExit(1)
```
