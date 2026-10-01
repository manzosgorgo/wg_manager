# `src/wg_frontend/check_vectors.mjs`

## Metadata

- Path: `src/wg_frontend/check_vectors.mjs`
- Language: `javascript`
- Lines: 121
- SHA256: `f272e66e8e522e525c1dbbde81a11b664028b11864accca94d15de2a2c758086`
- Imports:
  - `./wg_client_errors.js`
  - `./wg_secure_session.js`
  - `node:crypto`
  - `node:fs`

## Source

```javascript
// Verifica che wg_secure_session.js produca ESATTAMENTE gli stessi byte
// dell'implementazione Python di riferimento, usando il vettore canonico
// generato da wg_secure_session_gen_vectors.py (test_wg_secure_session_vectors.json).
//
// Eseguito con Node.js (usa crypto.webcrypto sotto il cofano), ma il
// modulo wg_secure_session.js sotto test usa solo API standard
// (crypto.subtle / crypto.getRandomValues) identiche a quelle di un
// browser: se questo script passa, il porting e' valido anche lato browser.

import { readFileSync } from "node:fs";
import { webcrypto } from "node:crypto";

// Rendiamo disponibile `crypto` come globale, esattamente come lo e' in
// un browser, cosi' wg_secure_session.js non ha bisogno di sapere se gira
// in Node o nel browser. Questo e' l'UNICO punto in cui Node entra in
// gioco: il modulo sotto test non ha piu' alcun fallback interno a
// require("node:crypto").
if (typeof globalThis.crypto === "undefined") {
  globalThis.crypto = webcrypto;
}
if (typeof globalThis.btoa === "undefined") {
  globalThis.btoa = (str) => Buffer.from(str, "binary").toString("base64");
}
if (typeof globalThis.atob === "undefined") {
  globalThis.atob = (str) => Buffer.from(str, "base64").toString("binary");
}

import { WGSecureSession, b64encode, bytesToHex, hexToBytes } from "./wg_secure_session.js";
import { WGReplayError } from "./wg_client_errors.js";

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    console.error(`[FAIL] ${label}`);
    console.error(`   atteso : ${expected}`);
    console.error(`   ottenuto: ${actual}`);
    process.exitCode = 1;
    return false;
  }
  console.log(`[PASS] ${label}`);
  return true;
}

async function main() {
  const vectors = JSON.parse(readFileSync(new URL("./test_wg_secure_session_vectors.json", import.meta.url)));

  // La configurazione e' source of truth, letta dal vettore canonico:
  // esattamente come Python, il modulo JS non ha piu' costanti hardcoded.
  const config = { secure_session: vectors.config };

  const kSession = hexToBytes(vectors.inputs.k_session_hex);
  const sessionId = hexToBytes(vectors.inputs.session_id_hex);

  const session = await WGSecureSession.create(config, kSession, sessionId);

  // --- confronto valori derivati intermedi ---
  assertEqual(bytesToHex(session._sessionSeed), vectors.derived.session_seed_hex, "session_seed");

  // request_key/response_key sono CryptoKey non estraibili: per
  // confrontarle dobbiamo verificarle indirettamente firmando lo stesso
  // messaggio del vettore Python e confrontando il MAC, non i byte grezzi
  // della chiave (che per progetto non sono esportabili). Vedi sotto.

  // --- vettore di richiesta ---
  const rv = vectors.request_vector;
  const reqNonce = hexToBytes(rv.nonce_hex);
  const reqBody = hexToBytes(rv.body_hex);

  const reqMessage = await session._requestMessage(rv.counter, reqNonce, rv.method, rv.path, reqBody);
  assertEqual(bytesToHex(reqMessage), rv.message_hex, "request message (formato byte-per-byte)");

  const reqMac = await session._sign(session._requestKey, reqMessage);
  assertEqual(bytesToHex(reqMac), rv.expected_mac_hex, "request MAC (== conferma indiretta di request_key)");

  assertEqual(session.sessionIdB64, rv.session_id_b64, "session_id (base64url)");
  assertEqual(b64encode(reqNonce), rv.nonce_b64, "nonce (base64url)");
  assertEqual(b64encode(reqMac), rv.mac_b64, "request mac (base64url)");

  // --- vettore di risposta ---
  const respv = vectors.response_vector;
  const respBody = hexToBytes(respv.body_hex);

  const respMessage = await session._responseMessage(respv.counter, reqNonce, respv.status, respBody);
  assertEqual(bytesToHex(respMessage), respv.message_hex, "response message (formato byte-per-byte)");

  const respMac = await session._sign(session._responseKey, respMessage);
  assertEqual(bytesToHex(respMac), respv.expected_mac_hex, "response MAC (== conferma indiretta di response_key)");
  assertEqual(b64encode(respMac), respv.mac_b64, "response mac (base64url)");

  // --- test funzionale end-to-end con l'API pubblica (non solo i metodi interni) ---
  const client = await WGSecureSession.create(config, kSession, sessionId);
  const server = await WGSecureSession.create(config, kSession, sessionId);

  const auth = await client.createRequestAuth("GET", "/api/ping", new TextEncoder().encode(""));
  const okReq = await server.verifyRequest(auth, "GET", "/api/ping", new TextEncoder().encode(""));
  assertEqual(okReq, true, "end-to-end: verifyRequest accetta una richiesta valida");

  const respAuth = await server.createResponseAuth(auth, 200, new TextEncoder().encode("pong"));
  const okResp = await client.verifyResponse(respAuth, auth, 200, new TextEncoder().encode("pong"));
  assertEqual(okResp, true, "end-to-end: verifyResponse accetta una risposta valida");

  // tampering: deve fallire
  try {
    await server.verifyRequest(auth, "GET", "/api/ping", new TextEncoder().encode(""));
    console.error("[FAIL] end-to-end: replay della stessa request non rilevato");
    process.exitCode = 1;
  } catch (e) {
    assertEqual(e.name, "WGReplayError", "end-to-end: replay della request rilevato con l'errore corretto");
    assertEqual(e instanceof WGReplayError, true, "end-to-end: l'errore di replay e' un'istanza di WGReplayError");
  }

  if (process.exitCode === 1) {
    console.log("\nAlcuni confronti sono falliti.");
  } else {
    console.log("\nTutti i vettori Python <-> JS combaciano byte-per-byte, ed il flusso end-to-end funziona.");
  }
}

main().catch((e) => {
  console.error("Errore inatteso durante la verifica:", e);
  process.exitCode = 1;
});
```
