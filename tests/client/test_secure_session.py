#!/usr/bin/env python3
"""
Test suite ampliata per WGSecureSession.

Organizzata per aree, in ordine di priorità concordato:
  1. response <-> request binding          (punto 9)
  2. semantica del counter                 (punto 6)
  3. tampering mirato (method/session-id)  (punti 3, 10)
  4. key/session isolation                 (punto 4, 5)
  5. nonce: binding e size                 (punto 8, parziale)
  6. input validation / errori strutturati (punti 11, 12, 13)

Convenzione: ogni test stampa "[PASS] ..." in caso di successo, così la
suite resta compatibile con lo stile dei test originali (eseguibili anche
come script, non solo con un runner tipo pytest/unittest).
"""

from src.wg_client.wg_secure_session import WGSecureSession
from src.wg_client.wg_client_errors import (
    WGMalformedMessageError,
    WGInvalidFieldError,
    WGInvalidEncodingError,
    WGCounterError,
    WGCounterExhaustedError,
    WGReplayError,
    WGSessionMismatchError,
    WGInvalidMACError,
)

K_SESSION = b"A" * 32
SESSION_ID = b"B" * 16

# Stessi default di wg_client.load_config(), riprodotti qui senza passare
# da un file di configurazione reale: WGSecureSession legge solo
# config["secure_session"][...], quindi basta questa sotto-struttura.
DEFAULT_SECURE_SESSION_CONFIG = {
    "session_id_size": 16,
    "nonce_size": 32,
    "session_key_size": 32,
    "counter_min": 1,
    "counter_max": 0xFFFFFFFF,
}

config = {
    "secure_session": dict(DEFAULT_SECURE_SESSION_CONFIG),
}


def new_pair(k_session: bytes = K_SESSION, session_id: bytes = SESSION_ID):
    """Crea una coppia client/server con lo stesso K_session/session_id."""
    client = WGSecureSession(config, k_session, session_id)
    server = WGSecureSession(config, k_session, session_id)
    return client, server


# ----------------------------------------------------------------------
# 1. Response <-> Request binding (priorità 9)
# ----------------------------------------------------------------------

def test_response_bound_to_its_own_request():
    """Il golden path: response creata per request_A si verifica con request_A."""
    client, server = new_pair()

    request_a = client.create_request_auth("GET", "/api/a", b"")
    server.verify_request(request_a, "GET", "/api/a", b"")
    response_a = server.create_response_auth(request_a, 200, b"OK")

    assert client.verify_response(response_a, request_a, 200, b"OK")

    print("[PASS] response verificata con la propria request")


def test_response_cannot_be_verified_with_different_request():
    """
    response_A creata in risposta a request_A NON deve poter essere
    verificata usando request_B, anche se request_B e' legittima e
    proviene dalla stessa sessione.
    """
    client, server = new_pair()

    request_a = client.create_request_auth("GET", "/api/a", b"")
    server.verify_request(request_a, "GET", "/api/a", b"")
    response_a = server.create_response_auth(request_a, 200, b"OK")

    request_b = client.create_request_auth("GET", "/api/b", b"")
    server.verify_request(request_b, "GET", "/api/b", b"")

    try:
        client.verify_response(response_a, request_b, 200, b"OK")
    except WGCounterError:
        print("[PASS] response_A rifiutata se abbinata a request_B (counter mismatch)")
        return

    raise AssertionError("response_A e' stata accettata insieme a request_B")


def test_response_nonce_is_inherited_from_request_not_from_auth():
    """
    La response non trasporta un proprio nonce: usa quello della request
    originale. Se il client verifica passando una request con lo stesso
    counter ma nonce diverso, la verifica deve fallire sul MAC.
    """
    client, server = new_pair()

    request_a = client.create_request_auth("GET", "/api/a", b"")
    server.verify_request(request_a, "GET", "/api/a", b"")
    response_a = server.create_response_auth(request_a, 200, b"OK")

    # Simuliamo una request "gemella" con stesso counter ma nonce diverso
    forged_request = dict(request_a)
    forged_request["nonce"] = client._b64(b"Z" * client.nonce_size)

    try:
        client.verify_response(response_a, forged_request, 200, b"OK")
    except WGInvalidMACError:
        print("[PASS] response rifiutata se il nonce della request non corrisponde")
        return

    raise AssertionError("response accettata con nonce di request alterato")


# ----------------------------------------------------------------------
# 2. Semantica del counter (priorita' 6)
# ----------------------------------------------------------------------

def test_request_counters_strictly_increasing_accepted():
    """Counter 1, 2, 3 in sequenza devono essere tutti accettati."""
    client, server = new_pair()

    for expected_counter in (1, 2, 3):
        auth = client.create_request_auth("GET", "/api/test", b"")
        assert auth["counter"] == expected_counter
        assert server.verify_request(auth, "GET", "/api/test", b"")

    print("[PASS] counter strettamente crescenti (1,2,3) accettati")


def test_request_counter_reordering_within_window_is_accepted():
    """Un counter piu' vecchio ma ancora nella window resta accettabile."""
    client, server = new_pair()
    auth1 = client.create_request_auth("GET", "/api/test", b"")
    auth2 = client.create_request_auth("GET", "/api/test", b"")
    server.verify_request(auth2, "GET", "/api/test", b"")

    assert server.verify_request(auth1, "GET", "/api/test", b"") is True
    print("[PASS] counter riordinato accettato nella replay window")


def test_request_counter_gaps_are_allowed_by_current_protocol():
    """
    Documenta esplicitamente la scelta di design attuale: il protocollo
    NON richiede counter contigui (counter == previous + 1), accetta
    "buchi" purche' il counter sia strettamente maggiore dell'ultimo
    accettato. Se in futuro si decide di richiedere contiguita' stretta,
    questo test va aggiornato per riflettere la nuova policy.
    """
    client, server = new_pair()
    auth_low = client.create_request_auth("GET", "/api/test", b"")
    server.verify_request(auth_low, "GET", "/api/test", b"")

    # Per testare "il counter puo' saltare" in modo coerente con il MAC,
    # simuliamo direttamente un secondo client sincronizzato che genera
    # un auth valido con un counter alto, forzando il contatore interno.
    client2, _ = new_pair()
    client2._request_counter = 99  # prossima chiamata produrra' counter=100
    auth_high = client2.create_request_auth("GET", "/api/test", b"")
    assert auth_high["counter"] == 100

    assert server.verify_request(auth_high, "GET", "/api/test", b"")

    print("[PASS] un salto di counter (buco) e' accettato")


def test_response_counter_must_match_request_counter():
    """auth di risposta con counter diverso da quello della request deve fallire."""
    client, server = new_pair()

    request_a = client.create_request_auth("GET", "/api/a", b"")
    server.verify_request(request_a, "GET", "/api/a", b"")
    response_a = server.create_response_auth(request_a, 200, b"OK")

    tampered_response = dict(response_a)
    tampered_response["counter"] = request_a["counter"] + 1

    try:
        client.verify_response(tampered_response, request_a, 200, b"OK")
    except WGCounterError:
        print("[PASS] response con counter non corrispondente alla request rifiutata")
        return

    raise AssertionError("response con counter alterato accettata")


def test_response_replay_detected():
    """La stessa response non puo' essere verificata due volte."""
    client, server = new_pair()

    request_a = client.create_request_auth("GET", "/api/a", b"")
    server.verify_request(request_a, "GET", "/api/a", b"")
    response_a = server.create_response_auth(request_a, 200, b"OK")

    client.verify_response(response_a, request_a, 200, b"OK")

    try:
        client.verify_response(response_a, request_a, 200, b"OK")
    except WGReplayError:
        print("[PASS] replay della response rilevato")
        return

    raise AssertionError("response replayata accettata")


# ----------------------------------------------------------------------
# 3. Tampering mirato: method e session_id (priorita' 3, 10)
# ----------------------------------------------------------------------

def test_request_method_tampering():
    """Verificare con un method diverso da quello firmato deve fallire."""
    client, server = new_pair()

    auth = client.create_request_auth("POST", "/api/test", b"hello")

    try:
        server.verify_request(auth, "GET", "/api/test", b"hello")
    except WGInvalidMACError:
        print("[PASS] method tampering rilevato")
        return

    raise AssertionError("tampering sul method accettato")


def test_request_session_id_tampering():
    """auth con session_id diverso da quello dell'istanza server deve fallire subito."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    other_session_id_b64 = WGSecureSession(config, K_SESSION, b"C" * 16).session_id_b64
    tampered = dict(auth)
    tampered["session_id"] = other_session_id_b64

    try:
        server.verify_request(tampered, "GET", "/api/test", b"")
    except WGSessionMismatchError:
        print("[PASS] session_id tampering su request rilevato")
        return

    raise AssertionError("request con session_id alterato accettata")


def test_response_session_id_tampering():
    """auth di risposta con session_id diverso deve fallire subito lato client."""
    client, server = new_pair()

    request_a = client.create_request_auth("GET", "/api/a", b"")
    server.verify_request(request_a, "GET", "/api/a", b"")
    response_a = server.create_response_auth(request_a, 200, b"OK")

    other_session_id_b64 = WGSecureSession(config, K_SESSION, b"C" * 16).session_id_b64
    tampered = dict(response_a)
    tampered["session_id"] = other_session_id_b64

    try:
        client.verify_response(tampered, request_a, 200, b"OK")
    except WGSessionMismatchError:
        print("[PASS] session_id tampering su response rilevato")
        return

    raise AssertionError("response con session_id alterato accettata")


# ----------------------------------------------------------------------
# 4. Key / session isolation (priorita' 4, 5)
# ----------------------------------------------------------------------

def test_same_key_different_session_id_fails():
    """Stesso K_session ma session_id diverso -> chiavi derivate diverse -> fail."""
    client_x = WGSecureSession(config, K_SESSION, b"X" * 16)
    server_y = WGSecureSession(config, K_SESSION, b"Y" * 16)

    auth = client_x.create_request_auth("GET", "/api/test", b"")

    try:
        server_y.verify_request(auth, "GET", "/api/test", b"")
    except WGSessionMismatchError:
        print("[PASS] stesso K_session, session_id diverso -> rifiutato")
        return

    raise AssertionError("sessioni con session_id diverso hanno prodotto auth compatibili")


def test_different_key_same_session_id_fails():
    """Session_id uguale ma K_session diverso -> chiavi derivate diverse -> fail."""
    client = WGSecureSession(config, b"A" * 32, SESSION_ID)
    server = WGSecureSession(config, b"Z" * 32, SESSION_ID)

    auth = client.create_request_auth("GET", "/api/test", b"")

    try:
        server.verify_request(auth, "GET", "/api/test", b"")
    except WGInvalidMACError:
        print("[PASS] stesso session_id, K_session diverso -> rifiutato")
        return

    raise AssertionError("sessioni con K_session diverso hanno prodotto auth compatibili")


def test_different_key_and_session_id_fails():
    """Caso combinato: ne' K_session ne' session_id coincidono."""
    client = WGSecureSession(config, b"A" * 32, b"X" * 16)
    server = WGSecureSession(config, b"Z" * 32, b"Y" * 16)

    auth = client.create_request_auth("GET", "/api/test", b"")

    try:
        server.verify_request(auth, "GET", "/api/test", b"")
    except WGSessionMismatchError:
        print("[PASS] K_session e session_id entrambi diversi -> rifiutato")
        return

    raise AssertionError("sessioni completamente diverse hanno prodotto auth compatibili")


def test_request_key_and_response_key_are_independent():
    """
    Verifica indiretta (senza esporre le chiavi private) che request_key e
    response_key siano derivate in modo indipendente: un auth di request
    non deve poter essere accettato come auth di response e viceversa,
    a parita' di messaggio firmato.
    """
    client, server = new_pair()

    request_a = client.create_request_auth("GET", "/api/a", b"")
    server.verify_request(request_a, "GET", "/api/a", b"")

    # Costruiamo un "finto" response_auth riusando counter/mac della request:
    # se le chiavi non fossero indipendenti, potrebbe passare la verifica
    # della response con lo stesso MAC calcolato per la request.
    forged_response = {
        "session_id": request_a["session_id"],
        "counter": request_a["counter"],
        "mac": request_a["mac"],
    }

    try:
        client.verify_response(forged_response, request_a, 200, b"")
    except WGInvalidMACError:
        print("[PASS] MAC di request non riutilizzabile come MAC di response")
        return

    raise AssertionError("un MAC di request e' stato accettato come MAC di response")


# ----------------------------------------------------------------------
# 5. Nonce (priorita' 8, parziale: binding, non analisi statistica)
# ----------------------------------------------------------------------

def test_nonce_has_expected_size():
    client, _ = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")
    nonce = client._unb64(auth["nonce"])

    assert len(nonce) == client.nonce_size

    print("[PASS] dimensione del nonce corretta")


def test_request_nonce_tampering_fails():
    """Modificare il nonce senza ricalcolare il MAC deve far fallire la verifica."""
    client, server = new_pair()
    auth = client.create_request_auth("GET", "/api/test", b"")

    tampered = dict(auth)
    tampered["nonce"] = client._b64(b"Z" * client.nonce_size)

    try:
        server.verify_request(tampered, "GET", "/api/test", b"")
    except WGInvalidMACError:
        print("[PASS] nonce tampering rilevato")
        return

    raise AssertionError("request con nonce alterato accettata")


# ----------------------------------------------------------------------
# 6. Input validation / errori strutturati (priorita' 11, 12, 13)
# ----------------------------------------------------------------------

def test_verify_request_with_missing_field():
    """Un campo obbligatorio mancante deve essere un messaggio malformato."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    incomplete = dict(auth)
    del incomplete["mac"]

    try:
        server.verify_request(incomplete, "GET", "/api/test", b"")
    except WGMalformedMessageError:
        print("[PASS] campo mancante -> WGMalformedMessageError")
        return

    raise AssertionError("campo mancante non rifiutato con WGMalformedMessageError")


def test_verify_request_with_non_dict_auth():
    """Un auth object che non sia un dict è un messaggio malformato."""
    _, server = new_pair()

    try:
        server.verify_request(None, "GET", "/api/test", b"")
    except WGMalformedMessageError:
        print("[PASS] auth non-dict -> WGMalformedMessageError")
        return

    raise AssertionError("auth non-dict accettato")


def test_verify_request_with_invalid_base64():
    """Base64 non valido deve produrre WGInvalidEncodingError."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    corrupted = dict(auth)
    corrupted["nonce"] = "!!!non-base64!!!"

    try:
        server.verify_request(corrupted, "GET", "/api/test", b"")
    except WGInvalidEncodingError:
        print("[PASS] base64 invalido -> WGInvalidEncodingError")
        return

    raise AssertionError("base64 invalido non rifiutato correttamente")


def test_verify_request_with_non_string_base64_field():
    """Un campo encoded non stringa deve essere un invalid field."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    corrupted = dict(auth)
    corrupted["nonce"] = b"not-a-string"

    try:
        server.verify_request(corrupted, "GET", "/api/test", b"")
    except WGInvalidFieldError:
        print("[PASS] campo Base64 non-stringa -> WGInvalidFieldError")
        return

    raise AssertionError("campo Base64 non-stringa accettato")


def test_verify_request_with_wrong_length_nonce():
    """Nonce Base64 valido ma di dimensione errata."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    corrupted = dict(auth)
    corrupted["nonce"] = client._b64(b"short")

    try:
        server.verify_request(corrupted, "GET", "/api/test", b"")
    except WGInvalidFieldError:
        print("[PASS] nonce di lunghezza errata -> WGInvalidFieldError")
        return

    raise AssertionError("nonce di lunghezza errata accettato")


def test_verify_request_with_wrong_length_mac():
    """MAC Base64 valido ma di dimensione errata."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    corrupted = dict(auth)
    corrupted["mac"] = client._b64(b"short")

    try:
        server.verify_request(corrupted, "GET", "/api/test", b"")
    except WGInvalidFieldError:
        print("[PASS] MAC di lunghezza errata -> WGInvalidFieldError")
        return

    raise AssertionError("MAC di lunghezza errata accettato")


def test_verify_request_with_invalid_counter_type():
    """Il counter deve essere un int e bool non deve essere accettato."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    for invalid_counter in ("1", 1.0, True, None):
        corrupted = dict(auth)
        corrupted["counter"] = invalid_counter

        try:
            server.verify_request(corrupted, "GET", "/api/test", b"")
        except WGInvalidFieldError:
            continue
        raise AssertionError(f"counter non valido accettato: {invalid_counter!r}")
    print("[PASS] tipi di counter non validi rifiutati")


def test_verify_request_with_counter_out_of_range():
    """Counter fuori dal range configurato deve produrre WGCounterError."""
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")
    for invalid_counter in (server.counter_min - 1, server.counter_max + 1):
        corrupted = dict(auth)
        corrupted["counter"] = invalid_counter

        try:
            server.verify_request(corrupted, "GET", "/api/test", b"")
        except WGCounterError:
            continue
        raise AssertionError(f"counter fuori range accettato: {invalid_counter}")
    print("[PASS] counter fuori range rifiutati")


def test_invalid_mac_does_not_advance_request_counter():
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    corrupted = dict(auth)
    corrupted["mac"] = client._b64(b"\x00" * client.MAC_SIZE)

    initial_counter = server._request_counter

    try:
        server.verify_request(corrupted, "GET", "/api/test", b"")
    except WGInvalidMACError:
        pass
    else:
        raise AssertionError("MAC invalido accettato")

    assert server._request_counter == initial_counter

    print("[PASS] MAC invalido non modifica il request counter")


def test_invalid_nonce_does_not_advance_request_counter():
    client, server = new_pair()

    auth = client.create_request_auth("GET", "/api/test", b"")

    corrupted = dict(auth)
    corrupted["nonce"] = client._b64(b"short")

    initial_counter = server._request_counter

    try:
        server.verify_request(corrupted, "GET", "/api/test", b"")
    except WGInvalidFieldError:
        pass
    else:
        raise AssertionError("nonce invalido accettato")

    assert server._request_counter == initial_counter

    print("[PASS] nonce invalido non modifica il request counter")


def test_request_path_tampering():
    client, server = new_pair()
    auth = client.create_request_auth("GET", "/api/original", b"hello")
    try:
        server.verify_request(auth, "GET", "/api/modified", b"hello")
    except WGInvalidMACError:
        print("[PASS] path tampering rilevato")
        return

    raise AssertionError("path tampering accettato")


def test_request_body_tampering():
    client, server = new_pair()
    auth = client.create_request_auth("POST", "/api/test", b"original")
    try:
        server.verify_request(auth, "POST", "/api/test", b"modified")
    except WGInvalidMACError:
        print("[PASS] body tampering rilevato")
        return

    raise AssertionError("body tampering accettato")


def test_response_status_tampering():
    client, server = new_pair()

    request = client.create_request_auth("GET", "/api/test", b"")
    server.verify_request(request, "GET", "/api/test", b"")

    response = server.create_response_auth(request, 200, b"OK")

    try:
        client.verify_response(response, request, 403, b"OK")
    except WGInvalidMACError:
        print("[PASS] response status tampering rilevato")
        return

    raise AssertionError("response status tampering accettato")


def test_response_body_tampering():
    client, server = new_pair()

    request = client.create_request_auth("GET", "/api/test", b"")
    server.verify_request(request, "GET", "/api/test", b"")

    response = server.create_response_auth(request, 200, b"OK")

    try:
        client.verify_response(response, request, 200, b"MODIFIED")
    except WGInvalidMACError:
        print("[PASS] response body tampering rilevato")
        return

    raise AssertionError("response body tampering accettato")


def test_request_counter_exhaustion():
    test_config = {
        **config,
        "secure_session": {
            **config["secure_session"],
            "counter_min": 1,
            "counter_max": 2,
        },
    }
    client = WGSecureSession(test_config, K_SESSION, SESSION_ID)
    auth1 = client.create_request_auth("GET", "/api/test", b"")
    assert auth1["counter"] == 1

    auth2 = client.create_request_auth("GET", "/api/test", b"")
    assert auth2["counter"] == 2

    try:
        client.create_request_auth("GET", "/api/test", b"")
    except WGCounterExhaustedError:
        print("[PASS] counter exhaustion rilevato")
        return

    raise AssertionError("counter exhaustion non rilevato")


# ----------------------------------------------------------------------
# Runner semplice (compatibile con lo stile dei test originali; con
# pytest questa sezione non viene eseguita, pytest scopre i test da solo)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        # 1. response <-> request binding
        test_response_bound_to_its_own_request,
        test_response_cannot_be_verified_with_different_request,
        test_response_nonce_is_inherited_from_request_not_from_auth,
        # 2. semantica del counter
        test_request_counters_strictly_increasing_accepted,
        test_request_counter_reordering_within_window_is_accepted,
        test_request_counter_gaps_are_allowed_by_current_protocol,
        test_response_counter_must_match_request_counter,
        test_response_replay_detected,
        # 3. tampering mirato
        test_request_method_tampering,
        test_request_session_id_tampering,
        test_response_session_id_tampering,
        # 4. key/session isolation
        test_same_key_different_session_id_fails,
        test_different_key_same_session_id_fails,
        test_different_key_and_session_id_fails,
        test_request_key_and_response_key_are_independent,
        # 5. nonce
        test_nonce_has_expected_size,
        test_request_nonce_tampering_fails,
        # 6. input validation / errori strutturati
        test_verify_request_with_missing_field,
        test_verify_request_with_non_dict_auth,
        test_verify_request_with_invalid_base64,
        test_verify_request_with_non_string_base64_field,
        test_verify_request_with_wrong_length_nonce,
        test_verify_request_with_wrong_length_mac,
        test_verify_request_with_invalid_counter_type,
        test_verify_request_with_counter_out_of_range,
        test_invalid_mac_does_not_advance_request_counter,
        test_invalid_nonce_does_not_advance_request_counter,
        test_request_path_tampering,
        test_request_body_tampering,
        test_response_status_tampering,
        test_response_body_tampering,
        test_request_counter_exhaustion,
    ]

    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"[FAIL] {test.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001 - vogliamo vedere anche errori non previsti
            failures += 1
            print(f"[ERROR] {test.__name__}: {type(exc).__name__}: {exc}")

    print()
    if failures:
        print(f"{failures} test falliti su {len(tests)}")
    else:
        print(f"Tutti i {len(tests)} test completati.")