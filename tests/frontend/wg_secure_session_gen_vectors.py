#!/usr/bin/env python3
"""
Genera il vettore canonico cross-language (Python <-> JS) per
WGSecureSession, a partire da un file di input che fissa:

  - la configurazione (session_id_size, nonce_size, session_key_size,
    counter_min, counter_max);
  - k_session e session_id;
  - il nonce da usare per la request (reso deterministico iniettando
    un rng fisso: NON e' un test del CSPRNG, e' un test vector);
  - method/path/body della request;
  - status/body della response.

L'output e' il formato canonico consumato da check_vectors.mjs:
test_wg_secure_session_vectors.json.

Uso:
    python3 wg_secure_session_gen_vectors.py <input.json> <output.json>
"""

import hashlib
import hmac
import json
import sys

from src.wg_client.wg_secure_session import WGSecureSession


def hex_to_bytes(value: str) -> bytes:
    return bytes.fromhex(value)


def bytes_to_hex(value: bytes) -> str:
    return value.hex()


def body_bytes(section: dict) -> bytes:
    """Il body puo' essere fornito come body_hex o come body_utf8."""
    if "body_hex" in section:
        return hex_to_bytes(section["body_hex"])
    return section.get("body_utf8", "").encode("utf-8")


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, value: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=2)
        f.write("\n")


def fixed_nonce_rng(nonce: bytes):
    """rng deterministico per rendere il vettore riproducibile: ignora
    la size richiesta e restituisce sempre lo stesso nonce (la size
    viene comunque validata a monte, nel main, contro config.nonce_size).
    """

    def _rng(size: int) -> bytes:
        assert size == len(nonce), "nonce_hex non corrisponde a config.nonce_size"
        return nonce

    return _rng


def generate_vector(input_data: dict) -> dict:
    config = {"secure_session": dict(input_data["config"])}

    k_session = hex_to_bytes(input_data["k_session_hex"])
    session_id = hex_to_bytes(input_data["session_id_hex"])
    nonce = hex_to_bytes(input_data["request"]["nonce_hex"])

    session = WGSecureSession(
        config,
        k_session,
        session_id,
        rng=fixed_nonce_rng(nonce),
    )

    method = input_data["request"]["method"]
    path = input_data["request"]["path"]
    req_body = body_bytes(input_data["request"])

    request_auth = session.create_request_auth(method, path, req_body)
    counter = request_auth["counter"]

    # message_hex / expected_mac_hex: ricalcolati con i metodi interni
    # cosi' check_vectors.mjs puo' confrontare byte-per-byte, prima
    # ancora di passare per l'API pubblica.
    req_message = session._request_message(counter, nonce, method, path, req_body)
    req_mac = hmac.digest(session._request_key, req_message, hashlib.sha256)
    assert bytes_to_hex(req_mac) == session._unb64(request_auth["mac"]).hex()

    status = input_data["response"]["status"]
    resp_body = body_bytes(input_data["response"])

    response_auth = session.create_response_auth(request_auth, status, resp_body)

    resp_message = session._response_message(counter, nonce, status, resp_body)
    resp_mac = hmac.digest(session._response_key, resp_message, hashlib.sha256)
    assert bytes_to_hex(resp_mac) == session._unb64(response_auth["mac"]).hex()

    return {
        "protocol_version": WGSecureSession.PROTOCOL_VERSION.decode("ascii"),
        "config": dict(input_data["config"]),
        "inputs": {
            "k_session_hex": input_data["k_session_hex"],
            "session_id_hex": input_data["session_id_hex"],
        },
        "derived": {
            "session_seed_hex": bytes_to_hex(session._session_seed),
        },
        "request_vector": {
            "counter": counter,
            "nonce_hex": bytes_to_hex(nonce),
            "method": method,
            "path": path,
            "body_hex": bytes_to_hex(req_body),
            "body_utf8": req_body.decode("utf-8", errors="replace"),
            "message_hex": bytes_to_hex(req_message),
            "expected_mac_hex": bytes_to_hex(req_mac),
            "session_id_b64": request_auth["session_id"],
            "nonce_b64": request_auth["nonce"],
            "mac_b64": request_auth["mac"],
        },
        "response_vector": {
            "counter": counter,
            "nonce_hex": bytes_to_hex(nonce),
            "status": status,
            "body_hex": bytes_to_hex(resp_body),
            "body_utf8": resp_body.decode("utf-8", errors="replace"),
            "message_hex": bytes_to_hex(resp_message),
            "expected_mac_hex": bytes_to_hex(resp_mac),
            "session_id_b64": response_auth["session_id"],
            "mac_b64": response_auth["mac"],
        },
    }


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "usage: wg_secure_session_gen_vectors.py <input.json> <output.json>",
            file=sys.stderr,
        )
        raise SystemExit(2)

    input_data = load_json(sys.argv[1])
    vector = generate_vector(input_data)
    save_json(sys.argv[2], vector)


if __name__ == "__main__":
    main()