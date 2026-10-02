#!/usr/bin/env python3
"""
Concurrency / ordering characterization tests for WGSecureSession as used
by the real WGClientAPIHandler.

Destinazione suggerita: tests/client/test_secure_session_concurrency.py

Nessun systemd, nessun TLS, nessuna rete esterna: WGClientHTTPServer viene
istanziato direttamente su 127.0.0.1:<porta libera> con un controller finto.

Convenzione:
  * i test verificano la replay window e la sicurezza dell'allocatore
    concorrente;
  * le richieste possono arrivare fuori ordine finche' restano nella
    replay window.

Per vedere il "report" dei risultati concorrenti:
    pytest tests/client/test_secure_session_concurrency.py -s -v
"""

import http.client
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.wg_client.wg_client_API_handler import (
    AUTH_COUNTER_HEADER,
    AUTH_MAC_HEADER,
    AUTH_NONCE_HEADER,
    AUTH_SESSION_ID_HEADER,
    WGClientAPIHandler,
    WGClientHTTPServer,
)
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
LISTEN_PATH = "/vpn-test"
INTERFACE = "wg0"


class FakePeerService:
    def status(self):
        return {"interface": INTERFACE, "peers": []}

    def add_peer(self, public_key, allowed_ip):
        return {"ok": True}

    def remove_peer(self, public_key):
        return {"ok": True}


def start_server():
    """Server HTTP reale con sessione sicura nuova (contatore del ricevente a zero)."""
    srv = WGClientHTTPServer(
        ("127.0.0.1", 0),
        WGClientAPIHandler,
        FakePeerService(),
        LISTEN_PATH,
        WGSecureSession(
            CFG,
            K_SESSION,
            SESSION_ID,
            principal={"username": "admin", "peers": []},
        ),
    )
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def stop_server(srv):
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def server():
    srv = start_server()
    yield srv
    stop_server(srv)


def new_sender():
    """Lato 'browser': stesso k_session e session_id del server."""
    return WGSecureSession(CFG, K_SESSION, SESSION_ID)


def sign(sender, method="GET", path="/v1/status", body=b""):
    return sender.create_request_auth(method, path, body)


SIGN_LOCK = threading.Lock()


def sign_serialized(sender, method="GET", path="/v1/status", body=b""):
    """Firma sotto lock: isola il riordino di rete dalla race lato mittente."""
    with SIGN_LOCK:
        return sender.create_request_auth(method, path, body)


def send(srv, auth, method="GET", path="/v1/status", body=b""):
    """Invia una richiesta gia' firmata; ritorna lo status HTTP."""
    port = srv.server_address[1]
    headers = {
        AUTH_SESSION_ID_HEADER: auth["session_id"],
        AUTH_COUNTER_HEADER: str(auth["counter"]),
        AUTH_NONCE_HEADER: auth["nonce"],
        AUTH_MAC_HEADER: auth["mac"],
    }
    if body:
        headers["Content-Length"] = str(len(body))
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, LISTEN_PATH + path, body=body or None, headers=headers)
        response = conn.getresponse()
        response.read()
        return response.status
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Baseline
# ----------------------------------------------------------------------

def test_sequential_requests_all_succeed(server):
    sender = new_sender()
    codes = [send(server, sign(sender)) for _ in range(20)]
    assert codes == [200] * 20


# ----------------------------------------------------------------------
# Guard: devono restare veri dopo la finestra
# ----------------------------------------------------------------------

def test_lost_request_does_not_desync(server):
    sender = new_sender()
    sign(sender)  # "persa": mai inviata
    assert send(server, sign(sender)) == 200


@pytest.mark.parametrize("round_", range(20))
def test_same_signed_request_sent_concurrently_accepted_once(server, round_):
    sender = new_sender()
    auth = sign(sender)
    barrier = threading.Barrier(8)

    def worker(_):
        barrier.wait()
        return send(server, auth)

    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(worker, range(8)))

    assert codes.count(200) == 1, Counter(codes)


def test_retry_with_same_counter_after_lost_response_is_rejected(server):
    sender = new_sender()
    auth = sign(sender)
    assert send(server, auth) == 200       # eseguita, ma "risposta persa"
    assert send(server, auth) == 401       # il retry deve usare un contatore nuovo
    assert send(server, sign(sender)) == 200


def test_python_sender_counters_unique_under_threads():
    """create_request_auth condiviso tra thread non deve duplicare contatori."""
    sender = new_sender()
    with ThreadPoolExecutor(16) as ex:
        auths = list(ex.map(lambda _: sign(sender), range(2000)))
    counters = [a["counter"] for a in auths]
    assert len(set(counters)) == len(counters)


# ----------------------------------------------------------------------
# Caratterizzazione: comportamento attuale che la finestra deve cambiare
# ----------------------------------------------------------------------

def test_reordered_pair_both_accepted_with_window(server):
    """Le richieste riordinate restano valide finche' sono nella window."""
    sender = new_sender()
    older = sign(sender)
    newer = sign(sender)
    assert send(server, newer) == 200
    assert send(server, older) == 200


def run_parallel(server, signer, n=64, workers=16):
    sender = new_sender()
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda _: send(server, signer(sender)), range(n)))


def test_concurrent_requests_report():
    """Non asserisce un esito preciso: stampa quante richieste falliscono.

    serialized     = firma sotto lock, invio parallelo -> misura SOLO il riordino di rete
    unsynchronized = firma e invio paralleli           -> race del mittente + riordino
    """
    for label, signer in (("serialized", sign_serialized), ("unsynchronized", sign)):
        srv = start_server()
        try:
            codes = run_parallel(srv, signer)
        finally:
            stop_server(srv)
        print(f"\nconcurrent, {label} signing -> {dict(Counter(codes))}")
        assert codes.count(200) >= 1
        assert set(codes) <= {200, 401}


def test_concurrent_requests_all_succeed_serialized_signing(server):
    codes = run_parallel(server, sign_serialized)
    assert set(codes) == {200}, Counter(codes)


def test_concurrent_requests_all_succeed_unsynchronized_signing(server):
    codes = run_parallel(server, sign)
    assert set(codes) == {200}, Counter(codes)