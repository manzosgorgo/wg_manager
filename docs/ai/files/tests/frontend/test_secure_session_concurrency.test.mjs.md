# `tests/frontend/test_secure_session_concurrency.test.mjs`

## Metadata

- Path: `tests/frontend/test_secure_session_concurrency.test.mjs`
- Language: `javascript`
- Lines: 113
- SHA256: `d7576d572e88294fb6c06665e87bfff5d7cfeaadb67857702327454652051f82`
- Imports:
  - `../../src/wg_frontend/wg_secure_session.js`
  - `node:assert`
  - `node:crypto`
  - `node:test`

## Source

```javascript
// Destinazione suggerita: tests/frontend/secure_session_concurrency.test.mjs
// Esecuzione:  node --test tests/frontend/
//
// createRequestAuth legge il contatore prima di due `await` (hash e firma)
// e lo assegna dopo: due chiamate concorrenti vedono lo stesso valore.
// Con il codice attuale il primo test deve FALLIRE.

import test from "node:test";
import assert from "node:assert";
import { webcrypto } from "node:crypto";

globalThis.crypto ??= webcrypto;

const { WGSecureSession } = await import("../../src/wg_frontend/wg_secure_session.js");

const CFG = {
    secure_session: {
        session_id_size: 16,
        nonce_size: 32,
        session_key_size: 32,
        counter_min: 1,
        counter_max: 0xffffffff,
    },
};

async function newSession() {
    const k = Uint8Array.from({ length: 32 }, (_, i) => i);
    return WGSecureSession.create(CFG, k, new Uint8Array(16));
}

test("createRequestAuth concorrenti non duplicano il contatore",
    async () => {
        const s = await newSession();
        const auths = await Promise.all(
            Array.from({ length: 20 }, () => s.createRequestAuth("GET", "/v1/status")),
        );
        const counters = auths.map((a) => a.counter);
        assert.strictEqual(new Set(counters).size, counters.length, `contatori: ${counters}`);
    });

test("createRequestAuth sequenziali: contatori consecutivi", async () => {
    const s = await newSession();
    const counters = [];
    for (let i = 0; i < 5; i++) {
        counters.push((await s.createRequestAuth("GET", "/v1/status")).counter);
    }
    assert.deepStrictEqual(counters, [1, 2, 3, 4, 5]);
});

test("verifyResponse concorrente della stessa risposta accettata una sola volta",
    async () => {
        const tx = await newSession();
        const rx = await newSession();

        const reqAuth = await tx.createRequestAuth("GET", "/v1/status");
        await rx.verifyRequest(reqAuth, "GET", "/v1/status");
        const respAuth = await rx.createResponseAuth(reqAuth, 200, new Uint8Array(0));

        const results = await Promise.allSettled(
            Array.from({ length: 8 }, () => tx.verifyResponse(respAuth, reqAuth, 200, new Uint8Array(0))),
        );
        const ok = results.filter((r) => r.status === "fulfilled").length;
        assert.strictEqual(ok, 1, `accettate: ${ok}`);
    });


test("verifyRequest accetta richieste concorrenti fuori ordine nella replay window", async () => {
    const tx = await newSession();
    const rx = await newSession();

    const auths = await Promise.all(
        Array.from({ length: 20 }, (_, i) =>
            tx.createRequestAuth("GET", `/v1/status/${i}`)
        ),
    );

    for (const auth of [...auths].reverse()) {
        const i = auth.counter - 1;
        assert.strictEqual(
            await rx.verifyRequest(auth, "GET", `/v1/status/${i}`),
            true,
        );
    }
});

test("verifyResponse accetta risposte concorrenti fuori ordine", async () => {
    const tx = await newSession();
    const rx = await newSession();

    const requests = await Promise.all(
        Array.from({ length: 20 }, (_, i) =>
            tx.createRequestAuth("GET", `/v1/status/${i}`)
        ),
    );

    await Promise.all(
        requests.map((auth, i) =>
            rx.verifyRequest(auth, "GET", `/v1/status/${i}`)
        ),
    );

    const responses = await Promise.all(
        requests.map((auth) => rx.createResponseAuth(auth, 200)),
    );

    for (const response of [...responses].reverse()) {
        const request = requests[response.counter - 1];
        assert.strictEqual(
            await tx.verifyResponse(response, request, 200),
            true,
        );
    }
});
```
