#!/usr/bin/env python3
"""
Thread-safety of WGSecureSession alone (no network, no HTTP handler).

Destinazione suggerita: tests/client/test_secure_session_threadsafety.py

Complementa test_secure_session_concurrency.py (che usa l'handler HTTP vero):
qui si verifica che lo STATO della sessione (contatori) resti coerente quando
piu' thread condividono la stessa istanza, sia come mittente sia come
ricevente. Non copre il riordino di rete: quello e' un problema di protocollo
(finestra di contatori), non di thread-safety.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.wg_client.wg_client_errors import WGReplayError
from src.wg_client.wg_secure_session import WGSecureSession

CFG = {
    "secure_session": {
        "session_id_size": 16,
        "nonce_size": 32,
        "session_key_size": 32,
        "counter_min": 1,
        "counter_max": 0xFFFFFFFF,
    }
}
K_SESSION = bytes(range(64))
SESSION_ID = bytes(16)


def new():
    return WGSecureSession(CFG, K_SESSION, SESSION_ID)


def run_threads(n, target):
    barrier = threading.Barrier(n)

    def worker():
        barrier.wait()
        return target()

    with ThreadPoolExecutor(n) as ex:
        futures = [ex.submit(worker) for _ in range(n)]
        return [f.result() for f in futures]


# ----------------------------------------------------------------------
# Mittente
# ----------------------------------------------------------------------

def test_sender_counters_unique_and_contiguous_under_threads():
    tx = new()
    with ThreadPoolExecutor(16) as ex:
        auths = list(ex.map(lambda _: tx.create_request_auth("GET", "/v1/status"), range(2000)))
    counters = sorted(a["counter"] for a in auths)
    assert counters == list(range(1, 2001))
    # lo stato interno non e' tornato indietro (lost update)
    assert tx.create_request_auth("GET", "/v1/status")["counter"] == 2001


def test_concurrently_created_requests_all_verify_when_delivered_in_order():
    tx, rx = new(), new()
    with ThreadPoolExecutor(8) as ex:
        auths = list(ex.map(lambda _: tx.create_request_auth("GET", "/a"), range(200)))
    for auth in sorted(auths, key=lambda a: a["counter"]):
        assert rx.verify_request(auth, "GET", "/a") is True


# ----------------------------------------------------------------------
# Ricevente
# ----------------------------------------------------------------------

@pytest.mark.parametrize("round_", range(50))
def test_verify_request_same_auth_concurrently_accepted_once(round_):
    tx, rx = new(), new()
    auth = tx.create_request_auth("GET", "/a")

    def attempt():
        try:
            return rx.verify_request(auth, "GET", "/a")
        except WGReplayError:
            return False

    results = run_threads(8, attempt)
    assert results.count(True) == 1, results


@pytest.mark.parametrize("round_", range(50))
def test_verify_response_same_auth_concurrently_accepted_once(round_):
    tx, rx = new(), new()
    request = tx.create_request_auth("GET", "/a")
    rx.verify_request(request, "GET", "/a")
    response = rx.create_response_auth(request, 200, b"")

    def attempt():
        try:
            return tx.verify_response(response, request, 200, b"")
        except WGReplayError:
            return False

    results = run_threads(8, attempt)
    assert results.count(True) == 1, results