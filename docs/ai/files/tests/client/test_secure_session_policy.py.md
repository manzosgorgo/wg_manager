# `tests/client/test_secure_session_policy.py`

## Metadata

- Path: `tests/client/test_secure_session_policy.py`
- Language: `python`
- Lines: 139
- SHA256: `4a941014c2b28fff5e9c4336e94226b4ab1376cbbb99398ef0769ae7c789b57b`
- Imports:
  - `pytest`
  - `src.wg_client.wg_client_errors`
  - `src.wg_client.wg_secure_session`

## Source

```python
#!/usr/bin/env python3

import pytest

from src.wg_client.wg_client_errors import (
    WGInvalidFieldError,
    WGRequestRateExceededError,
    WGSessionExpiredError,
    WGReplayError,
)
from src.wg_client.wg_secure_session import WGSecureSession


K_SESSION = b"A" * 64
SESSION_ID = b"B" * 16


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def cfg(**overrides):
    secure = {
        "session_id_size": 16,
        "nonce_size": 32,
        "session_key_size": 32,
        "counter_min": 1,
        "counter_max": 0xFFFFFFFF,
        "session_timeout": 86400,
        "max_request_frequency": 0.0,
        "replay_window_size": 64,
    }
    secure.update(overrides)
    return {"secure_session": secure}


def pair(**overrides):
    configuration = cfg(**overrides)
    clock = FakeClock()
    client = WGSecureSession(
        configuration, K_SESSION, SESSION_ID, clock=clock
    )
    server = WGSecureSession(
        configuration, K_SESSION, SESSION_ID, clock=clock
    )
    return client, server, clock


def test_reordered_request_within_window_is_accepted():
    client, server, _ = pair(replay_window_size=4)

    auths = [
        client.create_request_auth("GET", f"/{counter}")
        for counter in range(1, 4)
    ]

    assert server.verify_request(auths[2], "GET", "/3") is True
    assert server.verify_request(auths[0], "GET", "/1") is True
    assert server.verify_request(auths[1], "GET", "/2") is True


def test_request_older_than_window_is_rejected():
    client, server, _ = pair(replay_window_size=2)

    auths = [
        client.create_request_auth("GET", f"/{counter}")
        for counter in range(1, 5)
    ]

    assert server.verify_request(auths[3], "GET", "/4") is True

    with pytest.raises(WGReplayError):
        server.verify_request(auths[0], "GET", "/1")


def test_response_can_arrive_out_of_order():
    client, server, _ = pair(replay_window_size=4)

    requests = [
        client.create_request_auth("GET", f"/{counter}")
        for counter in range(1, 4)
    ]
    for request in requests:
        server.verify_request(request, "GET", f"/{request['counter']}")

    responses = [
        server.create_response_auth(request, 200, b"")
        for request in requests
    ]

    assert client.verify_response(responses[1], requests[1], 200, b"") is True
    assert client.verify_response(responses[0], requests[0], 200, b"") is True
    assert client.verify_response(responses[2], requests[2], 200, b"") is True


def test_session_expiry_is_enforced():
    client, _, clock = pair(session_timeout=10)

    assert client.create_request_auth("GET", "/a")["counter"] == 1
    clock.advance(10)

    with pytest.raises(WGSessionExpiredError):
        client.create_request_auth("GET", "/b")


def test_max_request_frequency_is_enforced_without_a_timer_thread():
    client, _, clock = pair(
        session_timeout=100,
        max_request_frequency=10.0,
    )

    assert client.create_request_auth("GET", "/1")["counter"] == 1

    with pytest.raises(WGRequestRateExceededError):
        client.create_request_auth("GET", "/2")

    clock.advance(0.1)
    assert client.create_request_auth("GET", "/2")["counter"] == 2


def test_frequency_and_timeout_must_fit_counter_capacity():
    with pytest.raises(WGInvalidFieldError):
        WGSecureSession(
            cfg(
                counter_min=1,
                counter_max=10,
                session_timeout=10,
                max_request_frequency=2.0,
            ),
            K_SESSION,
            SESSION_ID,
        )
```
