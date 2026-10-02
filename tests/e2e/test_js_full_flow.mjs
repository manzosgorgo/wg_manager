#!/usr/bin/env node

import assert from "node:assert/strict";
import crypto, { webcrypto } from "node:crypto";
import fs from "node:fs";
import https from "node:https";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

if (typeof globalThis.crypto === "undefined") {
  globalThis.crypto = webcrypto;
}


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "../..");

const require = createRequire(import.meta.url);
const OPAQUE_HELPER = path.join(ROOT, "tests/auth/js/opaque_client.js");
const AUTH_HELPER = path.join(ROOT, "tests/auth/js/wg_auth_client.js");

for (const helper of [OPAQUE_HELPER, AUTH_HELPER]) {
  if (!fs.existsSync(helper)) {
    throw new Error(
      `missing E2E helper: ${helper}; restore tests/auth/js before running this test`
    );
  }
}

const { OpaqueClient } = require(OPAQUE_HELPER);
const { WGAuthHTTPClient } = require(AUTH_HELPER);

const {
  WGSecureSession,
  hexToBytes,
} = await import("../../src/wg_frontend/wg_secure_session.js");

const AUTH_CONF = path.join(ROOT, "tests/auth/js/test_auth.conf");
const CLIENT_CONF = path.join(ROOT, "config/wg-client-test-auth.conf");

const CERT = path.join(ROOT, "cert/client.crt");
const KEY = path.join(ROOT, "cert/client.key");
const LOGIN_DIR = path.join(ROOT, "login");
const PEER_REGISTRY = path.join(LOGIN_DIR, ".peer_registry.json");

function parseIni(filename) {
  const config = {};
  let section = null;

  for (const raw of fs.readFileSync(filename, "utf8").split(/\r?\n/)) {
    const line = raw.trim();

    if (!line || line.startsWith("#") || line.startsWith(";")) continue;

    if (line.startsWith("[") && line.endsWith("]")) {
      section = line.slice(1, -1).trim();
      config[section] ??= {};
      continue;
    }

    const pos = line.indexOf("=");
    if (pos < 0 || !section) continue;

    config[section][line.slice(0, pos).trim()] =
      line.slice(pos + 1).trim();
  }

  return config;
}

function secureSessionConfig(clientConfig) {
  const sc = clientConfig.secure_session;

  return {
    secure_session: {
      session_id_size: Number(sc.session_id_size),
      nonce_size: Number(sc.nonce_size),
      session_key_size: Number(sc.session_key_size),
      counter_min: Number(sc.counter_min),
      counter_max: Number(sc.counter_max),
      session_timeout: Number(sc.session_timeout ?? 86400),
      max_request_frequency: Number(sc.max_request_frequency ?? 0),
      replay_window_size: Number(sc.replay_window_size ?? 64),
    },
  };
}

function requestHttps({ port, method, requestPath, headers = {}, body = null }) {
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: "127.0.0.1",
      port,
      path: requestPath,
      method,
      cert: fs.readFileSync(CERT),
      key: fs.readFileSync(KEY),
      rejectUnauthorized: false,
      headers,
    }, (res) => {
      const chunks = [];

      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve({
        status: res.statusCode,
        headers: res.headers,
        body: Buffer.concat(chunks),
      }));
    });

    req.setTimeout(10000, () => {
      req.destroy(new Error("HTTP request timeout"));
    });

    req.on("error", reject);

    if (body) req.write(body);
    req.end();
  });
}

async function secureRequest(session, listenPath, port, method, apiPath, object = null) {
  const body = object === null
    ? Buffer.alloc(0)
    : Buffer.from(JSON.stringify(object), "utf8");

  const auth = await session.createRequestAuth(
    method,
    apiPath,
    new Uint8Array(body),
  );

  const headers = {
    Accept: "application/json",
    Connection: "close",
    "X-WG-Session-ID": auth.session_id,
    "X-WG-Counter": String(auth.counter),
    "X-WG-Nonce": auth.nonce,
    "X-WG-MAC": auth.mac,
  };

  if (body.length) {
    headers["Content-Type"] = "application/json";
    headers["Content-Length"] = String(body.length);
  }

  const response = await requestHttps({
    port,
    method,
    requestPath: listenPath + apiPath,
    headers,
    body: body.length ? body : null,
  });

  const responseAuth = {
    session_id: response.headers["x-wg-session-id"],
    counter: Number(response.headers["x-wg-counter"]),
    mac: response.headers["x-wg-mac"],
  };

  assert.ok(responseAuth.session_id, "missing authenticated response session id");
  assert.ok(Number.isInteger(responseAuth.counter), "missing authenticated response counter");
  assert.ok(responseAuth.mac, "missing authenticated response MAC");

  await session.verifyResponse(
    responseAuth,
    auth,
    response.status,
    new Uint8Array(response.body),
  );

  let data = null;
  if (response.body.length) {
    data = JSON.parse(response.body.toString("utf8"));
  }

  return { status: response.status, data };
}

function userPeers(username) {
  const filename = path.join(LOGIN_DIR, username);
  const record = JSON.parse(fs.readFileSync(filename, "utf8"));
  assert.ok(Array.isArray(record.peers), "user record peers must be an array");
  return record.peers;
}

function registryEntry(publicKey) {
  if (!fs.existsSync(PEER_REGISTRY)) return null;
  const registry = JSON.parse(fs.readFileSync(PEER_REGISTRY, "utf8"));
  return registry.peers?.[publicKey] ?? null;
}

function findFreeIp(status, extraUsed = []) {
  const used = new Set(extraUsed);

  for (const peer of status.peers ?? []) {
    for (const allowed of peer.allowed_ips ?? []) {
      const match = /^10\.8\.0\.(\d+)\/32$/.exec(allowed);
      if (match) used.add(Number(match[1]));
    }
  }

  for (let host = 2; host <= 254; host++) {
    if (!used.has(host)) return `10.8.0.${host}/32`;
  }

  throw new Error("no free address in 10.8.0.0/24");
}

async function waitForLoggedOut(authClient) {
  for (let i = 0; i < 50; i++) {
    const status = await authClient.status();
    if (
      status.status === 200 &&
      status.data?.authenticated === false &&
      status.data?.client_active === false
    ) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  throw new Error("session did not shut down");
}

async function main() {
  const authConfig = parseIni(AUTH_CONF);
  const clientConfig = parseIni(CLIENT_CONF);

  const username = authConfig.auth.username;
  const password = authConfig.auth.password;
  const authUrl = authConfig.server.url;

  const authClient = new WGAuthHTTPClient(authUrl);
  let authenticated = false;
  let createdPeer = null;
  let session = null;
  let listenPath = "/postauth";
  const clientPort = 9444;

  try {
    if (clientConfig.secure_session?.enabled?.toLowerCase() !== "true") {
      throw new Error(
        "config/wg-client-test-auth.conf must have [secure_session] enabled = true"
      );
    }

    console.log("[1/10] OPAQUE authentication");

    const opaque = new OpaqueClient(username, password);
    const startRequest = await opaque.start();

    const start = await authClient.request("POST", "/auth", {
      username,
      pub: startRequest.pub,
    });

    assert.equal(start.status, 200, JSON.stringify(start.data));

    const credentials = opaque.finish(start.data.response);

    const finish = await authClient.request("POST", "/auth/verify", {
      auth: credentials.auth,
    });

    assert.equal(finish.status, 200, JSON.stringify(finish.data));
    assert.equal(finish.data?.ok, true);
    authenticated = true;

    assert.equal(
      credentials.sessionKey,
      finish.data.k_session,
      "client/server OPAQUE K_session mismatch",
    );
    assert.equal(credentials.sessionKey.length, 128, "OPAQUE K_session must be 64 bytes");

    console.log("[2/10] client/server K_session match");

    session = await WGSecureSession.create(
      secureSessionConfig(clientConfig),
      hexToBytes(credentials.sessionKey),
      hexToBytes(finish.data.session_id),
    );

    console.log("[3/10] authenticated GET /v1/status");

    const initial = await secureRequest(
      session,
      listenPath,
      clientPort,
      "GET",
      "/v1/status",
    );

    assert.equal(initial.status, 200);
    assert.equal(initial.data?.ok, true);
    assert.ok(Array.isArray(initial.data?.peers));

    const allowedIp = findFreeIp(initial.data);
    const publicKey = crypto.randomBytes(32).toString("base64");
    createdPeer = publicKey;
    const peerPath = "/v1/peers/" + encodeURIComponent(publicKey);

    console.log(`[4/10] PUT peer ${publicKey} -> ${allowedIp}`);

    const added = await secureRequest(
      session,
      listenPath,
      clientPort,
      "PUT",
      peerPath,
      {
        public_key: publicKey,
        allowed_ip: allowedIp,
      },
    );

    assert.equal(added.status, 200, JSON.stringify(added.data));
    assert.equal(added.data?.ok, true);
    assert.equal(added.data?.public_key, publicKey);
    assert.ok(
      userPeers(username).includes(publicKey),
      "new peer ownership was not persisted",
    );
    assert.deepEqual(
      registryEntry(publicKey),
      {
        username,
        allowed_ip: allowedIp,
        ownership_state: "consistent",
      },
      "peer reservation was not persisted",
    );

    console.log("[5/10] duplicate IP is rejected before manager");
    const duplicateIpKey = crypto.randomBytes(32).toString("base64");
    const duplicateIp = await secureRequest(
      session,
      listenPath,
      clientPort,
      "PUT",
      "/v1/peers/" + encodeURIComponent(duplicateIpKey),
      {
        public_key: duplicateIpKey,
        allowed_ip: allowedIp,
      },
    );
    assert.equal(duplicateIp.status, 409, JSON.stringify(duplicateIp.data));

    console.log("[6/10] duplicate key is rejected before manager");
    const alternateIp = findFreeIp(initial.data, [allowedIp]);
    const duplicateKey = await secureRequest(
      session,
      listenPath,
      clientPort,
      "PUT",
      peerPath,
      {
        public_key: publicKey,
        allowed_ip: alternateIp,
      },
    );
    assert.equal(duplicateKey.status, 409, JSON.stringify(duplicateKey.data));

    console.log("[7/10] GET verifies peer exists");

    const afterAdd = await secureRequest(
      session,
      listenPath,
      clientPort,
      "GET",
      "/v1/status",
    );

    assert.equal(afterAdd.status, 200);
    assert.ok(
      afterAdd.data.peers.some((peer) => peer.public_key === publicKey),
      "new peer is missing from status",
    );

    console.log("[8/10] DELETE peer");

    const removed = await secureRequest(
      session,
      listenPath,
      clientPort,
      "DELETE",
      peerPath,
    );

    assert.equal(removed.status, 200, JSON.stringify(removed.data));
    assert.equal(removed.data?.ok, true);
    assert.ok(
      !userPeers(username).includes(publicKey),
      "deleted peer ownership is still persisted",
    );
    assert.equal(
      registryEntry(publicKey),
      null,
      "deleted peer reservation is still persisted",
    );

    createdPeer = null;

    console.log("[9/10] GET verifies peer disappeared");

    const afterDelete = await secureRequest(
      session,
      listenPath,
      clientPort,
      "GET",
      "/v1/status",
    );

    assert.equal(afterDelete.status, 200);
    assert.ok(
      !afterDelete.data.peers.some((peer) => peer.public_key === publicKey),
      "deleted peer is still visible",
    );

    console.log("[10/10] logout");

    const logout = await secureRequest(
      session,
      listenPath,
      clientPort,
      "DELETE",
      "/v1/session",
    );
    assert.equal(logout.status, 200, JSON.stringify(logout.data));
    authenticated = false;

    await waitForLoggedOut(authClient);

    console.log("E2E JS FULL FLOW: PASS");
  } finally {
    if (createdPeer && session) {
      try {
        const peerPath = "/v1/peers/" + encodeURIComponent(createdPeer);
        await secureRequest(
          session,
          listenPath,
          clientPort,
          "DELETE",
          peerPath,
        );
      } catch {
        // Best-effort cleanup; preserve the original test failure.
      }
    }

    if (authenticated && session) {
      try {
        await secureRequest(
          session,
          listenPath,
          clientPort,
          "DELETE",
          "/v1/session",
        );
        await waitForLoggedOut(authClient);
      } catch {
        // Best-effort cleanup; idle timeout remains the final fallback.
      }
    }

  }
}

main().catch((error) => {
  console.error("E2E JS FULL FLOW: FAIL");
  console.error(error.stack || error);
  process.exit(1);
});
