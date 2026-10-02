#!/usr/bin/env node

import assert from "node:assert/strict";
import crypto, { webcrypto } from "node:crypto";
import fs from "node:fs";
import https from "node:https";
import path from "node:path";
import { spawnSync } from "node:child_process";
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
const LOGIN_DIR = path.join(ROOT, "login");
const CERT = path.join(ROOT, "cert/client.crt");
const KEY = path.join(ROOT, "cert/client.key");

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

async function secureRequest(session, listenPath, port, method, apiPath) {
  const body = Buffer.alloc(0);
  const auth = await session.createRequestAuth(
    method,
    apiPath,
    new Uint8Array(body),
  );

  const response = await requestHttps({
    port,
    method,
    requestPath: listenPath + apiPath,
    headers: {
      Accept: "application/json",
      Connection: "close",
      "X-WG-Session-ID": auth.session_id,
      "X-WG-Counter": String(auth.counter),
      "X-WG-Nonce": auth.nonce,
      "X-WG-MAC": auth.mac,
    },
  });

  const responseAuth = {
    session_id: response.headers["x-wg-session-id"],
    counter: Number(response.headers["x-wg-counter"]),
    mac: response.headers["x-wg-mac"],
  };

  await session.verifyResponse(
    responseAuth,
    auth,
    response.status,
    new Uint8Array(response.body),
  );

  return {
    status: response.status,
    data: response.body.length
      ? JSON.parse(response.body.toString("utf8"))
      : null,
  };
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

function manageUser(args, password = null) {
  const result = spawnSync(
    process.env.PYTHON ?? "python3",
    [
      "tools/manage_users.py",
      "--login-dir",
      LOGIN_DIR,
      ...args,
    ],
    {
      cwd: ROOT,
      input: password === null ? undefined : password + "\n",
      encoding: "utf8",
    },
  );

  assert.equal(
    result.status,
    0,
    result.stderr || result.stdout || "user management command failed",
  );
}

async function main() {
  const authConfig = parseIni(AUTH_CONF);
  const clientConfig = parseIni(CLIENT_CONF);
  const authUrl = authConfig.server.url;

  const username = `e2e-${process.pid}-${crypto.randomBytes(4).toString("hex")}`;
  const password = `E2E-${crypto.randomBytes(16).toString("hex")}`;
  const userFile = path.join(LOGIN_DIR, username);

  const authClient = new WGAuthHTTPClient(authUrl);
  let authenticated = false;
  let session = null;

  try {
    console.log("[1/5] create temporary user");
    manageUser(
      ["create", username, "--password-stdin"],
      password,
    );
    assert.ok(fs.existsSync(userFile), "user record was not created");

    console.log("[2/5] authenticate temporary user");
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
    authenticated = true;

    console.log("[3/5] access wg-client with new account");
    session = await WGSecureSession.create(
      secureSessionConfig(clientConfig),
      hexToBytes(credentials.sessionKey),
      hexToBytes(finish.data.session_id),
    );

    const status = await secureRequest(
      session,
      "/postauth",
      9444,
      "GET",
      "/v1/status",
    );

    assert.equal(status.status, 200, JSON.stringify(status.data));
    assert.equal(status.data?.ok, true);
    assert.deepEqual(status.data?.peers, []);

    console.log("[4/5] logout temporary user");
    const logout = await secureRequest(
      session,
      "/postauth",
      9444,
      "DELETE",
      "/v1/session",
    );
    assert.equal(logout.status, 200, JSON.stringify(logout.data));
    authenticated = false;
    await waitForLoggedOut(authClient);

    console.log("[5/5] delete temporary user");
    manageUser(["delete", username]);
    assert.ok(!fs.existsSync(userFile), "user record was not deleted");

    console.log("E2E JS USER LIFECYCLE: PASS");

  } finally {
    if (authenticated) {
      try {
        await authClient.logout();
        await waitForLoggedOut(authClient);
      } catch {
        // Preserve original failure.
      }
    }

    if (fs.existsSync(userFile)) {
      try {
        manageUser(["delete", username]);
      } catch {
        // Preserve original failure.
      }
    }
  }
}

main().catch((error) => {
  console.error("E2E JS USER LIFECYCLE: FAIL");
  console.error(error.stack || error);
  process.exit(1);
});
