import { WGOPAQUEClient } from "./wg_opaque_client.js";

export class WGAuthSession {
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

    async status() {
        return this._request("GET", "/status");
    }

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

    async logout() {
        try {
            return await this._request("DELETE", "/auth");
        } finally {
            this.username = null;
            this.sessionId = null;
            this.kSession = null;
            this.activation = null;
        }
    }

    async resetServerSession() {
        return this.logout();
    }
}
