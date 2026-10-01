import json
import ssl
import threading
import time
import urllib.error
import urllib
import json
import subprocess
from pathlib import Path.request

import pytest


AUTH_URL = "https://127.0.0.1:9445"
VALID_ID = "test-user"

TLS_CONTEXT = ssl._create_unverified_context()

REQUEST_TIMEOUT = 10
STATE_TIMEOUT = 10


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NODE_CLIENT = PROJECT_ROOT / "tests" / "auth" / "js" / "client_cli.js"

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def node_client(action):
    result = subprocess.run(
        ["node", str(NODE_CLIENT), action],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=REQUEST_TIMEOUT,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"node client failed:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    return json.loads(result.stdout)
def authenticate():
    result = node_client("authenticate")

    return (
        result["status"],
        result["data"],
    )
def request(method, path, data=None):
    url = AUTH_URL + path

    body = None
    headers = {}

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            req,
            context=TLS_CONTEXT,
            timeout=REQUEST_TIMEOUT,
        ) as response:
            payload = response.read()

            return {
                "method": method,
                "path": path,
                "status": response.status,
                "payload": json.loads(payload),
                "exception": None,
            }

    except urllib.error.HTTPError as exc:
        payload = exc.read()

        return {
            "method": method,
            "path": path,
            "status": exc.code,
            "payload": json.loads(payload),
            "exception": None,
        }

    except Exception as exc:
        return {
            "method": method,
            "path": path,
            "status": None,
            "payload": None,
            "exception": exc,
        }


def get_status():
    result = request("GET", "/status")

    assert result["exception"] is None, (
        f"/status failed: {result['exception']!r}"
    )

    assert result["status"] == 200, (
        f"/status returned {result['status']}: "
        f"{result['payload']!r}"
    )

    return result["payload"]


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def wait_for_state(authenticated, client_active, timeout=STATE_TIMEOUT):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            status = get_status()

            if (
                status["authenticated"] == authenticated
                and status["client_active"] == client_active
            ):
                return status

        except AssertionError:
            pass

        time.sleep(0.05)

    status = get_status()

    pytest.fail(
        "timeout waiting for state "
        f"(authenticated={authenticated}, "
        f"client_active={client_active}); "
        f"actual={status!r}"
    )


def assert_coherent_status():
    status = get_status()

    assert status["authenticated"] == status["client_active"], (
        f"incoherent session state: {status!r}"
    )

    return status


def cleanup_session():
    result = request("DELETE", "/auth")

    # DELETE is intentionally idempotent.
    if result["exception"] is not None:
        return

    wait_for_state(False, False)


@pytest.fixture(autouse=True)
def clean_state():
    cleanup_session()

    yield

    cleanup_session()


# ---------------------------------------------------------------------------
# Concurrent execution helper
# ---------------------------------------------------------------------------

def run_concurrently(*operations):
    """
    Run all operations simultaneously.

    The barrier is the synchronization mechanism of the test.
    No systemd operation is used as a synchronization primitive.
    """

    barrier = threading.Barrier(len(operations))

    results = [None] * len(operations)
    threads = []

    def worker(index, operation):
        try:
            barrier.wait()

            result = operation()

            results[index] = result

        except BaseException as exc:
            results[index] = {
                "method": "<worker>",
                "path": "<unknown>",
                "status": None,
                "payload": None,
                "exception": exc,
            }

    for index, operation in enumerate(operations):
        thread = threading.Thread(
            target=worker,
            args=(index, operation),
            name=f"race-worker-{index}",
        )

        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join(timeout=REQUEST_TIMEOUT + 2)

    for index, thread in enumerate(threads):
        assert not thread.is_alive(), (
            f"race worker {index} did not terminate"
        )

    return results


def assert_no_request_exceptions(results):
    failures = [
        result
        for result in results
        if result is None or result["exception"] is not None
    ]

    assert not failures, (
        "request exceptions/timeouts occurred:\n"
        + "\n".join(repr(item) for item in failures)
    )


# ---------------------------------------------------------------------------
# AUTH × AUTH
# ---------------------------------------------------------------------------

def test_concurrent_auth():
    results = run_concurrently(
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
    )

    assert_no_request_exceptions(results)

    statuses = sorted(result["status"] for result in results)

    assert statuses == [200, 409], results

    wait_for_state(True, True)


# ---------------------------------------------------------------------------
# DELETE × DELETE
# ---------------------------------------------------------------------------

def test_concurrent_logout():
    result = request(
        "POST",
        "/auth",
        {"fake_id": VALID_ID},
    )

    assert result["exception"] is None
    assert result["status"] == 200

    wait_for_state(True, True)

    results = run_concurrently(
        lambda: request("DELETE", "/auth"),
        lambda: request("DELETE", "/auth"),
    )

    assert_no_request_exceptions(results)

    assert all(
        result["status"] == 200
        for result in results
    ), results

    wait_for_state(False, False)


# ---------------------------------------------------------------------------
# AUTH × DELETE
# ---------------------------------------------------------------------------

def test_auth_delete_race():
    results = run_concurrently(
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
        lambda: request("DELETE", "/auth"),
    )

    assert_no_request_exceptions(results)

    auth_result = results[0]
    logout_result = results[1]

    assert auth_result["status"] in (200, 409), results
    assert logout_result["status"] == 200, results

    # Either operation may logically win.
    # What must never happen is an incoherent externally visible state.
    status = assert_coherent_status()

    if status["authenticated"]:
        wait_for_state(True, True)
    else:
        wait_for_state(False, False)


# ---------------------------------------------------------------------------
# AUTH × STATUS
# ---------------------------------------------------------------------------

def test_auth_status_race():
    results = run_concurrently(
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
        lambda: request("GET", "/status"),
    )

    assert_no_request_exceptions(results)

    status_result = results[1]

    assert status_result["status"] == 200

    status = status_result["payload"]

    assert status["authenticated"] == status["client_active"]

    # The GET is allowed to observe either side of the transition.
    assert status["authenticated"] in (True, False)


# ---------------------------------------------------------------------------
# DELETE × STATUS
# ---------------------------------------------------------------------------

def test_logout_status_race():
    result = request(
        "POST",
        "/auth",
        {"fake_id": VALID_ID},
    )

    assert result["exception"] is None
    assert result["status"] == 200

    wait_for_state(True, True)

    results = run_concurrently(
        lambda: request("DELETE", "/auth"),
        lambda: request("GET", "/status"),
    )

    assert_no_request_exceptions(results)

    status_result = results[1]

    assert status_result["status"] == 200

    status = status_result["payload"]

    assert status["authenticated"] == status["client_active"]

    wait_for_state(False, False)


# ---------------------------------------------------------------------------
# AUTH × DELETE × AUTH
# ---------------------------------------------------------------------------

def test_auth_delete_auth_race():
    results = run_concurrently(
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
        lambda: request("DELETE", "/auth"),
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
    )

    assert_no_request_exceptions(results)

    auth_results = [
        result
        for result in results
        if result["method"] == "POST"
    ]

    assert len(auth_results) == 2

    assert all(
        result["status"] in (200, 409)
        for result in auth_results
    )

    status = assert_coherent_status()

    if status["authenticated"]:
        wait_for_state(True, True)
    else:
        wait_for_state(False, False)


# ---------------------------------------------------------------------------
# Repeated sequential lifecycle
# ---------------------------------------------------------------------------

def test_repeated_auth_logout():
    for iteration in range(10):
        result = request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        )

        assert result["exception"] is None, (
            f"iteration {iteration}: {result!r}"
        )

        assert result["status"] == 200, (
            f"iteration {iteration}: {result!r}"
        )

        wait_for_state(True, True)

        result = request("DELETE", "/auth")

        assert result["exception"] is None, (
            f"iteration {iteration}: {result!r}"
        )

        assert result["status"] == 200, (
            f"iteration {iteration}: {result!r}"
        )

        wait_for_state(False, False)


# ---------------------------------------------------------------------------
# Repeated AUTH × AUTH
# ---------------------------------------------------------------------------

def test_concurrent_auth_stress():
    for iteration in range(5):
        results = run_concurrently(
            lambda: request(
                "POST",
                "/auth",
                {"fake_id": VALID_ID},
            ),
            lambda: request(
                "POST",
                "/auth",
                {"fake_id": VALID_ID},
            ),
        )

        assert_no_request_exceptions(results)

        statuses = sorted(
            result["status"]
            for result in results
        )

        assert statuses == [200, 409], (
            f"iteration {iteration}: {results!r}"
        )

        wait_for_state(True, True)

        cleanup_session()


# ---------------------------------------------------------------------------
# Repeated DELETE × DELETE
# ---------------------------------------------------------------------------

def test_concurrent_logout_stress():
    for iteration in range(5):
        result = request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        )

        assert result["exception"] is None
        assert result["status"] == 200

        wait_for_state(True, True)

        results = run_concurrently(
            lambda: request("DELETE", "/auth"),
            lambda: request("DELETE", "/auth"),
        )

        assert_no_request_exceptions(results)

        assert all(
            result["status"] == 200
            for result in results
        ), f"iteration {iteration}: {results!r}"

        wait_for_state(False, False)


# ---------------------------------------------------------------------------
# Mixed stress
# ---------------------------------------------------------------------------

def test_mixed_race_stress():
    """
    Exercise several legal concurrent transitions.

    The test deliberately does not require a specific winner.
    It only checks that the final externally visible state is coherent.
    """

    operations = [
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
        lambda: request("DELETE", "/auth"),
        lambda: request("GET", "/status"),
        lambda: request(
            "POST",
            "/auth",
            {"fake_id": VALID_ID},
        ),
        lambda: request("GET", "/status"),
    ]

    for iteration in range(5):
        results = run_concurrently(*operations)

        assert_no_request_exceptions(results)

        for result in results:
            if result["method"] == "GET":
                assert result["status"] == 200

                status = result["payload"]

                assert (
                    status["authenticated"]
                    == status["client_active"]
                )

            elif result["method"] == "POST":
                assert result["status"] in (200, 409)

            elif result["method"] == "DELETE":
                assert result["status"] == 200

        status = assert_coherent_status()

        if status["authenticated"]:
            wait_for_state(True, True)
        else:
            wait_for_state(False, False)

        cleanup_session()