/**
 * Browser-side OPAQUE authentication orchestration for wg-auth.\nKeeps the resulting session identifier, shared session key and activation metadata only in memory.
 * @module wg_auth_session
 */
import { WGOPAQUEClient } from "./wg_opaque_client.js";

/**
 * One browser authentication session against wg-auth.
 */
export class WGAuthSession {
    /**
     * @param {string} [baseUrl=""] Base URL prepended to wg-auth endpoints.
     */
    constructor(baseUrl = "") {
        this.baseUrl = baseUrl.replace(/\/$/, "");
        this.sessionId = null;
        this.kSession = null;
        this.activation = null;
        this.username = null;
    }

    async _request(method, path, body = null) {
        const options = {
            method,
            headers: {
                Accept: "application/json",
            },
        };

        if (body !== null) {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(body);
        }

        const response = await fetch(this.baseUrl + path, options);
        const text = await response.text();

        let data = null;
        if (text) {
            try {
                data = JSON.parse(text);
            } catch {
                throw new Error(
                    `invalid JSON response from ${path}: ${text}`
                );
            }
        }

        return {
            status: response.status,
            ok: response.ok,
            data,
        };
    }

    /**
     * Read coarse authentication/client activation state from wg-auth.
     * @returns {Promise<{status:number, ok:boolean, data:Object|null}>}
     */
    async status() {
        return this._request("GET", "/status");
    }

    /**
     * Complete the two-message OPAQUE login and persist session material in memory.
     *
     * The client and server OPAQUE session keys are compared before the session
     * is accepted. A mismatch is treated as a fatal authentication failure.
     *
     * @param {string} username
     * @param {string} password
     * @returns {Promise<Object>} wg-auth verification/activation response.
     * @throws {Error} If OPAQUE or either HTTP phase fails.
     */
    async authenticate(username, password) {
        const opaque = new WGOPAQUEClient(username, password);
        const startRequest = await opaque.start();

        const start = await this._request(
            "POST",
            "/auth",
            {
                username,
                pub: startRequest.pub,
            },
        );

        if (!start.ok || !start.data?.ok) {
            throw new Error(
                start.data?.error ?? `authentication start failed (${start.status})`
            );
        }

        const credentials = opaque.finish(start.data.response);

        const finish = await this._request(
            "POST",
            "/auth/verify",
            {
                auth: credentials.auth,
            },
        );

        if (!finish.ok || !finish.data?.ok) {
            throw new Error(
                finish.data?.error ?? `authentication failed (${finish.status})`
            );
        }

        if (finish.data.k_session !== credentials.sessionKey) {
            try {
                await this._request("DELETE", "/auth");
            } catch {
                // Best-effort rollback: preserve the original mismatch error.
            }

            throw new Error("OPAQUE client/server session key mismatch");
        }

        this.username = username;
        this.sessionId = finish.data.session_id;
        this.kSession = credentials.sessionKey;
        this.activation = finish.data.activation ?? null;

        return {
            ...finish.data,
            session_id: this.sessionId,
            k_session: this.kSession,
        };
    }

    /**
     * Erase all browser-held authentication/session material.
     * @returns {void}
     */
    clear() {
        this.username = null;
        this.sessionId = null;
        this.kSession = null;
        this.activation = null;
    }
}
