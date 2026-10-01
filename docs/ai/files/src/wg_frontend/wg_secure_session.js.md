# `src/wg_frontend/wg_secure_session.js`

## Metadata

- Path: `src/wg_frontend/wg_secure_session.js`
- Language: `javascript`
- Lines: 683
- SHA256: `d60b75a740d9f448f798f0199177a391d0bb3fed2ce01e69b99adf71f01f9df7`

## Source

```javascript
/**
 * WGSecureSession — porting JavaScript (Web Crypto API) del modulo Python
 * src/wg_client/wg_secure_session.py
 *
 * Progettato per girare identico sia in un browser moderno (crypto.subtle
 * globale) sia in Node.js (crypto.webcrypto esposto come globalThis.crypto
 * dal chiamante, vedi check_vectors.mjs) — nessuna libreria esterna, e
 * nessun fallback Node interno al modulo: il modulo usa esclusivamente
 * l'API Web Crypto standard.
 *
 * Il protocollo (formato dei messaggi, HKDF con questi salt/info, contatori,
 * dimensione di nonce/chiavi, configurazione, gerarchia di errori) e'
 * IDENTICO alla versione Python: le due implementazioni devono produrre
 * esattamente gli stessi byte per gli stessi input, e sollevare lo stesso
 * "tipo" di errore (per nome di classe) per la stessa condizione. Vedi
 * check_vectors.mjs per la verifica automatica contro i vettori generati
 * dall'implementazione Python.
 *
 * Come in Python, la configurazione (session_id_size, nonce_size,
 * session_key_size, counter_min, counter_max) e' source of truth e viene
 * passata dal chiamante — non ci sono costanti hardcoded nel modulo.
 *
 * Differenze deliberate rispetto alla versione Python, dovute all'ambiente:
 *   - Le chiavi derivate (request_key/response_key) sono importate come
 *     CryptoKey non estraibili (extractable: false), per non lasciarle
 *     leggibili come bytes grezzi a un eventuale script malevolo nella
 *     stessa pagina (mitigazione parziale, non totale, di un XSS).
 *   - Le API di SubtleCrypto sono asincrone: tutti i metodi che calcolano
 *     o verificano un MAC restituiscono una Promise, e la costruzione
 *     dell'istanza avviene tramite la factory asincrona
 *     WGSecureSession.create(...) invece che nel costruttore.
 */

import {
  WGProtocolError,
  WGMalformedMessageError,
  WGInvalidFieldError,
  WGInvalidEncodingError,
  WGCounterError,
  WGCounterExhaustedError,
  WGAuthenticationError,
  WGInvalidMACError,
  WGSessionMismatchError,
  WGReplayError,
  WGSessionExpiredError,
  WGRequestRateExceededError,
} from "./wg_client_errors.js";

// ----------------------------------------------------------------------
// Helper: risoluzione dell'oggetto SubtleCrypto e del CSPRNG
//
// Nessun fallback Node.js qui dentro: il modulo deve restare
// autenticamente browser-compatible. E' compito del chiamante Node
// (vedi check_vectors.mjs) esporre `globalThis.crypto = webcrypto`
// prima di importare questo modulo.
// ----------------------------------------------------------------------

function getSubtle() {
  if (!globalThis.crypto?.subtle) {
    throw new Error("Web Crypto API is not available (globalThis.crypto.subtle)");
  }
  return globalThis.crypto.subtle;
}

function getRandomBytes(size) {
  if (!globalThis.crypto?.getRandomValues) {
    throw new Error("Web Crypto API is not available (globalThis.crypto.getRandomValues)");
  }
  return globalThis.crypto.getRandomValues(new Uint8Array(size));
}

// ----------------------------------------------------------------------
// Helper: encoding
// ----------------------------------------------------------------------

const textEncoder = new TextEncoder();

function concatBytes(...arrays) {
  const total = arrays.reduce((sum, a) => sum + a.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const a of arrays) {
    out.set(a, offset);
    offset += a.length;
  }
  return out;
}

function bytesToHex(bytes) {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function hexToBytes(hex) {
  if (hex.length % 2 !== 0) {
    throw new WGProtocolError("hex string must have even length");
  }
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return out;
}

// Base64 URL-safe, equivalente a base64.urlsafe_b64encode/decode di Python
function b64encode(bytes) {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  const standard = btoa(binary);
  return standard.replace(/\+/g, "-").replace(/\//g, "_");
}

function b64decode(str) {
  if (typeof str !== "string") {
    throw new WGInvalidFieldError("encoded value must be a string");
  }
  let standard = str.replace(/-/g, "+").replace(/_/g, "/");
  while (standard.length % 4 !== 0) {
    standard += "=";
  }
  let binary;
  try {
    binary = atob(standard);
  } catch (e) {
    throw new WGInvalidEncodingError("invalid base64 encoding");
  }
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function sha256(bytes) {
  const subtle = getSubtle();
  const digest = await subtle.digest("SHA-256", bytes);
  return new Uint8Array(digest);
}

// MAC size e' una proprieta' dell'algoritmo (HMAC-SHA256), non della
// configurazione — identico a MAC_SIZE in Python.
const MAC_SIZE = 32;

// ----------------------------------------------------------------------
// Classe principale
// ----------------------------------------------------------------------

const PROTOCOL_VERSION = textEncoder.encode("wg_manager secure session v1");

export class WGSecureSession {
  /**
   * Costruttore "privato": usare WGSecureSession.create(...), perche'
   * la derivazione delle chiavi con SubtleCrypto e' asincrona e un
   * costruttore JS non puo' essere async.
   */
  constructor(config, sessionId, sessionSeed, requestKey, responseKey, rng, clock) {
    this._config = config;

    this.sessionIdSize = config.secure_session.session_id_size;
    this.nonceSize = config.secure_session.nonce_size;
    this.keySize = config.secure_session.session_key_size;
    this.counterMin = config.secure_session.counter_min;
    this.counterMax = config.secure_session.counter_max;
    this.sessionTimeout = config.secure_session.session_timeout ?? 86400;
    this.maxRequestFrequency = config.secure_session.max_request_frequency ?? 0.0;
    this.replayWindowSize = config.secure_session.replay_window_size ?? 64;
    this.MAC_SIZE = MAC_SIZE;

    this._sessionId = sessionId; // Uint8Array
    this._sessionSeed = sessionSeed; // Uint8Array (esposto solo per debug/test-vector)
    this._requestKey = requestKey; // CryptoKey (HMAC)
    this._responseKey = responseKey; // CryptoKey (HMAC)

    this._requestCounter = this.counterMin - 1;
    this._pendingRequests = {};

    this._requestReceiveHighest = this.counterMin - 1;
    this._requestReceiveAccepted = new Set();
    this._responseReceiveHighest = this.counterMin - 1;
    this._responseReceiveAccepted = new Set();

    this._rng = rng || getRandomBytes;
    this._clock = clock || (() => (
      globalThis.performance?.now ? globalThis.performance.now() / 1000 : Date.now() / 1000
    ));
    this._sessionStarted = this._clock();
    this._sessionExpiresAt = this._sessionStarted + this.sessionTimeout;

    // Serializes the check -> await -> commit sequences of verification.
    this._verifyChain = Promise.resolve();
  }

  /**
   * Factory asincrona, con la stessa forma del costruttore Python:
   * (config, k_session, session_id=None, rng=None).
   *
   * kSession e sessionId sono Uint8Array. config e' un oggetto con la
   * stessa forma di quello letto da Python: config.secure_session = {
   *   session_id_size, nonce_size, session_key_size, counter_min, counter_max
   * }.
   *
   * `rng`, se fornito, e' una funzione (size) => Uint8Array usata SOLO
   * per generare il nonce in createRequestAuth — non per il session_id
   * di default, esattamente come in Python. Serve unicamente per i
   * test a vettori deterministici; il default e' il CSPRNG del Web
   * Crypto standard.
   */
  static async create(config, kSession, sessionId = null, rng = null, clock = null) {
    const sc = config?.secure_session;
    if (!sc) {
      throw new WGInvalidFieldError('config.secure_session is required');
    }

    const sessionIdSize = sc.session_id_size;
    const nonceSize = sc.nonce_size;
    const keySize = sc.session_key_size;
    const counterMin = sc.counter_min;
    const counterMax = sc.counter_max;
    const sessionTimeout = sc.session_timeout ?? 86400;
    const maxRequestFrequency = sc.max_request_frequency ?? 0.0;
    const replayWindowSize = sc.replay_window_size ?? 64;

    if (!Number.isInteger(sessionTimeout) || sessionTimeout <= 0) {
      throw new WGInvalidFieldError("invalid session timeout");
    }
    if (!Number.isFinite(maxRequestFrequency) || maxRequestFrequency < 0) {
      throw new WGInvalidFieldError("invalid maximum request frequency");
    }
    if (!Number.isInteger(replayWindowSize) || replayWindowSize <= 0) {
      throw new WGInvalidFieldError("invalid replay window size");
    }

    const counterCapacity = counterMax - counterMin + 1;
    if (maxRequestFrequency > 0 && maxRequestFrequency * sessionTimeout > counterCapacity) {
      throw new WGInvalidFieldError("maximum request frequency and session timeout exceed counter capacity");
    }

    if (counterMin < 1) {
      throw new WGInvalidFieldError("invalid counter minimum");
    }
    if (counterMax < counterMin) {
      throw new WGInvalidFieldError("invalid counter range");
    }
    if (counterMax > 0xffffffff) {
      throw new WGInvalidFieldError("counter maximum exceeds uint32 range");
    }

    if (!(kSession instanceof Uint8Array)) {
      throw new WGInvalidFieldError("k_session must be a Uint8Array");
    }
    if (kSession.length !== keySize) {
      throw new WGInvalidFieldError(`k_session must be ${keySize} bytes`);
    }

    if (sessionId === null) {
      sessionId = getRandomBytes(sessionIdSize);
    }
    if (!(sessionId instanceof Uint8Array)) {
      throw new WGInvalidFieldError("session_id must be a Uint8Array");
    }
    if (sessionId.length !== sessionIdSize) {
      throw new WGInvalidFieldError(`session_id must be ${sessionIdSize} bytes`);
    }

    const subtle = getSubtle();

    // --- HKDF: session_seed = HKDF-SHA256(salt=session_id, info=PROTOCOL_VERSION, ikm=k_session) ---
    const ikmKey = await subtle.importKey("raw", kSession, "HKDF", false, ["deriveBits"]);

    const sessionSeedBits = await subtle.deriveBits(
      {
        name: "HKDF",
        hash: "SHA-256",
        salt: sessionId,
        info: PROTOCOL_VERSION,
      },
      ikmKey,
      keySize * 8,
    );
    const sessionSeed = new Uint8Array(sessionSeedBits);

    // --- HKDF: request_key / response_key derivate da session_seed, salt=null (== salt di zeri) ---
    const seedKey = await subtle.importKey("raw", sessionSeed, "HKDF", false, ["deriveBits"]);

    const requestKeyBits = await subtle.deriveBits(
      {
        name: "HKDF",
        hash: "SHA-256",
        salt: new Uint8Array(0),
        info: concatBytes(PROTOCOL_VERSION, textEncoder.encode("|"), textEncoder.encode("request authentication")),
      },
      seedKey,
      keySize * 8,
    );

    const responseKeyBits = await subtle.deriveBits(
      {
        name: "HKDF",
        hash: "SHA-256",
        salt: new Uint8Array(0),
        info: concatBytes(PROTOCOL_VERSION, textEncoder.encode("|"), textEncoder.encode("response authentication")),
      },
      seedKey,
      keySize * 8,
    );

    // Chiavi HMAC non estraibili: il codice JS della pagina puo' USARLE
    // per firmare/verificare, ma non puo' leggerne il valore grezzo
    // (mitigazione parziale in caso di XSS).
    const requestKey = await subtle.importKey(
      "raw",
      requestKeyBits,
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign", "verify"],
    );
    const responseKey = await subtle.importKey(
      "raw",
      responseKeyBits,
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign", "verify"],
    );

    return new WGSecureSession(
      config, sessionId, new Uint8Array(sessionSeed), requestKey, responseKey, rng, clock
    );
  }

  get sessionId() {
    return this._sessionId;
  }

  get sessionIdB64() {
    return b64encode(this._sessionId);
  }

  // ------------------------------------------------------------------
  // Autenticazione richieste
  // ------------------------------------------------------------------

  async createRequestAuth(method, path, body = new Uint8Array(0)) {
    if (typeof method !== "string") throw new WGInvalidFieldError("method must be str");
    if (typeof path !== "string") throw new WGInvalidFieldError("path must be str");
    if (!(body instanceof Uint8Array)) throw new WGInvalidFieldError("body must be bytes");

    // Reserve the counter synchronously, BEFORE the first await.
    // A burned counter is harmless because receivers accept gaps.
    this._checkSessionActive();
    if (this._requestCounter >= this.counterMax) {
      throw new WGCounterExhaustedError("request counter exhausted");
    }
    this._checkRequestRate();

    const counter = ++this._requestCounter;
    const nonce = this._rng(this.nonceSize);

    const message = await this._requestMessage(counter, nonce, method, path, body);
    const mac = await this._sign(this._requestKey, message);

    const auth = {
      session_id: this.sessionIdB64,
      counter,
      nonce: b64encode(nonce),
      mac: b64encode(mac),
    };
    this._pendingRequests[counter] = { ...auth };
    return auth;
  }

  async verifyRequest(auth, method, path, body = new Uint8Array(0)) {
    if (typeof method !== "string") throw new WGInvalidFieldError("method must be str");
    if (typeof path !== "string") throw new WGInvalidFieldError("path must be str");
    if (!(body instanceof Uint8Array)) throw new WGInvalidFieldError("body must be bytes");

    const validated = this._validateRequestAuth(auth);

    if (!bytesEqual(validated.session_id, this._sessionId)) {
      throw new WGSessionMismatchError("invalid session id");
    }

    // The replay check and the counter commit must not interleave with
    // another verification (there are awaits in between).
    return this._withVerifyLock(async () => {
      this._checkSessionActive();
      const counter = validated.counter;

      if (!this._counterInReceiveWindow(counter, this._requestReceiveHighest)) {
        throw new WGReplayError("request counter outside replay window");
      }
      if (this._requestReceiveAccepted.has(counter)) {
        throw new WGReplayError("request counter replayed");
      }

      const message = await this._requestMessage(counter, validated.nonce, method, path, body);
      const valid = await this._verify(this._requestKey, validated.mac, message);

      if (!valid) {
        throw new WGInvalidMACError("invalid request MAC");
      }

      this._acceptReceiveCounter(counter, true);
      return true;
    });
  }

  // ------------------------------------------------------------------
  // Autenticazione risposte
  // ------------------------------------------------------------------

  async createResponseAuth(requestAuth, status, body = new Uint8Array(0)) {
    if (!Number.isInteger(status)) throw new WGInvalidFieldError("status must be int");
    if (!(body instanceof Uint8Array)) throw new WGInvalidFieldError("body must be bytes");

    const validatedRequest = this._validateRequestAuth(requestAuth);

    if (!bytesEqual(validatedRequest.session_id, this._sessionId)) {
      throw new WGSessionMismatchError("invalid session id");
    }

    this._checkSessionActive();
    const counter = validatedRequest.counter;
    const nonce = validatedRequest.nonce;

    const message = await this._responseMessage(counter, nonce, status, body);
    const mac = await this._sign(this._responseKey, message);

    return {
      session_id: this.sessionIdB64,
      counter,
      mac: b64encode(mac),
    };
  }

  async verifyResponse(auth, requestAuth, status, body = new Uint8Array(0)) {
    if (!Number.isInteger(status)) throw new WGInvalidFieldError("status must be int");
    if (!(body instanceof Uint8Array)) throw new WGInvalidFieldError("body must be bytes");

    const validatedAuth = this._validateResponseAuth(auth);
    const validatedRequest = this._validateRequestAuth(requestAuth);

    if (!bytesEqual(validatedRequest.session_id, this._sessionId)) {
      throw new WGSessionMismatchError("invalid request session id");
    }
    if (!bytesEqual(validatedAuth.session_id, this._sessionId)) {
      throw new WGSessionMismatchError("invalid response session id");
    }
    if (!bytesEqual(validatedAuth.session_id, validatedRequest.session_id)) {
      throw new WGSessionMismatchError("request/response session mismatch");
    }

    if (validatedAuth.counter !== validatedRequest.counter) {
      throw new WGCounterError("response counter does not match request");
    }

    return this._withVerifyLock(async () => {
      this._checkSessionActive();
      const counter = validatedAuth.counter;

      if (!this._counterInReceiveWindow(counter, this._responseReceiveHighest)) {
        throw new WGReplayError("response counter outside replay window");
      }
      if (this._responseReceiveAccepted.has(counter)) {
        throw new WGReplayError("response replayed");
      }

      if (!(counter in this._pendingRequests)) {
        throw new WGCounterError("response does not correspond to a pending request");
      }

      const nonce = validatedRequest.nonce;

      const message = await this._responseMessage(counter, nonce, status, body);
      const valid = await this._verify(this._responseKey, validatedAuth.mac, message);

      if (!valid) {
        throw new WGInvalidMACError("invalid response MAC");
      }

      this._acceptReceiveCounter(counter, false);
      delete this._pendingRequests[counter];
      return true;
    });
  }

  // ------------------------------------------------------------------
  // Session lifecycle and replay windows
  // ------------------------------------------------------------------

  _checkSessionActive() {
    if (this._clock() >= this._sessionExpiresAt) {
      throw new WGSessionExpiredError("secure session expired");
    }
  }

  _checkRequestRate() {
    if (this.maxRequestFrequency <= 0) return;

    const elapsed = Math.max(0, this._clock() - this._sessionStarted);
    const requestsUsed = this._requestCounter - this.counterMin + 1;
    const allowed = Math.floor(elapsed * this.maxRequestFrequency) + 1;

    if (requestsUsed >= allowed) {
      throw new WGRequestRateExceededError("maximum request frequency exceeded");
    }
  }

  _counterInReceiveWindow(counter, highestSeen) {
    const lowerBound = Math.max(
      this.counterMin,
      highestSeen - this.replayWindowSize + 1,
    );
    return lowerBound <= counter && counter <= this.counterMax;
  }

  _acceptReceiveCounter(counter, request) {
    const accepted = request
      ? this._requestReceiveAccepted
      : this._responseReceiveAccepted;

    let highest = request
      ? this._requestReceiveHighest
      : this._responseReceiveHighest;

    if (counter > highest) highest = counter;

    accepted.add(counter);
    const lowerBound = Math.max(
      this.counterMin,
      highest - this.replayWindowSize + 1,
    );

    for (const value of Array.from(accepted)) {
      if (value < lowerBound) accepted.delete(value);
    }

    if (request) {
      this._requestReceiveHighest = highest;
    } else {
      this._responseReceiveHighest = highest;
    }
  }

  // ------------------------------------------------------------------
  // Field validation (equivalenti a _validate_* in Python)
  // ------------------------------------------------------------------

  // Runs fn once every previously queued verification has settled, so
  // the replay check and the counter commit of two verifications can
  // never interleave.
  _withVerifyLock(fn) {
    const run = this._verifyChain.then(fn);
    this._verifyChain = run.catch(() => {});
    return run;
  }

  _validateAuthStructure(auth, requiredFields) {
    if (auth === null || typeof auth !== "object" || Array.isArray(auth)) {
      throw new WGMalformedMessageError("auth must be an object");
    }
    for (const field of requiredFields) {
      if (!(field in auth)) {
        throw new WGMalformedMessageError(`missing field: ${field}`);
      }
    }
  }

  _validateSessionId(value) {
    const sessionId = b64decode(value);
    if (sessionId.length !== this.sessionIdSize) {
      throw new WGInvalidFieldError(`session_id must be ${this.sessionIdSize} bytes`);
    }
    return sessionId;
  }

  _validateCounter(value) {
    if (typeof value !== "number" || !Number.isInteger(value)) {
      throw new WGInvalidFieldError("counter must be int");
    }
    if (value < this.counterMin || value > this.counterMax) {
      throw new WGCounterError("counter out of valid range");
    }
    return value;
  }

  _validateNonce(value) {
    const nonce = b64decode(value);
    if (nonce.length !== this.nonceSize) {
      throw new WGInvalidFieldError(`nonce must be ${this.nonceSize} bytes`);
    }
    return nonce;
  }

  _validateMac(value) {
    const mac = b64decode(value);
    if (mac.length !== this.MAC_SIZE) {
      throw new WGInvalidFieldError(`mac must be ${this.MAC_SIZE} bytes`);
    }
    return mac;
  }

  _validateRequestAuth(auth) {
    this._validateAuthStructure(auth, ["session_id", "counter", "nonce", "mac"]);
    return {
      session_id: this._validateSessionId(auth.session_id),
      counter: this._validateCounter(auth.counter),
      nonce: this._validateNonce(auth.nonce),
      mac: this._validateMac(auth.mac),
    };
  }

  _validateResponseAuth(auth) {
    this._validateAuthStructure(auth, ["session_id", "counter", "mac"]);
    return {
      session_id: this._validateSessionId(auth.session_id),
      counter: this._validateCounter(auth.counter),
      mac: this._validateMac(auth.mac),
    };
  }

  // ------------------------------------------------------------------
  // Interni: costruzione messaggi (deve restare byte-per-byte identica
  // alla versione Python)
  // ------------------------------------------------------------------

  async _requestMessage(counter, nonce, method, path, body) {
    const bodyHash = await sha256(body);
    return concatBytes(
      this._sessionId,
      textEncoder.encode("|"),
      textEncoder.encode(String(counter)),
      textEncoder.encode("|"),
      nonce,
      textEncoder.encode("|"),
      textEncoder.encode(method),
      textEncoder.encode("|"),
      textEncoder.encode(path),
      textEncoder.encode("|"),
      bodyHash,
    );
  }

  async _responseMessage(counter, nonce, status, body) {
    const bodyHash = await sha256(body);
    return concatBytes(
      this._sessionId,
      textEncoder.encode("|"),
      textEncoder.encode(String(counter)),
      textEncoder.encode("|"),
      nonce,
      textEncoder.encode("|"),
      textEncoder.encode(String(status)),
      textEncoder.encode("|"),
      bodyHash,
    );
  }

  async _sign(key, message) {
    const subtle = getSubtle();
    const sig = await subtle.sign("HMAC", key, message);
    return new Uint8Array(sig);
  }

  async _verify(key, mac, message) {
    const subtle = getSubtle();
    // subtle.verify fa gia' un confronto a tempo costante internamente
    return subtle.verify("HMAC", key, mac, message);
  }
}

function bytesEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a[i] ^ b[i];
  }
  return diff === 0;
}

export { b64encode, b64decode, bytesToHex, hexToBytes };
```
