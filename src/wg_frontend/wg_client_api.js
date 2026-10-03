/**
 * Authenticated browser client for the per-session wg-client HTTPS API.\nSigns canonical API targets with WGSecureSession and verifies every authenticated response before JSON decoding.
 * @module wg_client_api
 */
import {
    WGSecureSession,
    hexToBytes,
} from "./wg_secure_session.js";

const textEncoder = new TextEncoder();

/** Default browser-side secure-session parameters matching production Python defaults. */
export const DEFAULT_SECURE_SESSION_CONFIG = {
    secure_session: {
        session_id_size: 16,
        nonce_size: 32,
        session_key_size: 32,
        counter_min: 1,
        counter_max: 4294967295,
    },
};

/**
 * High-level authenticated API client used by the VPN frontend.
 */
export class WGClientAPI {
    /**
     * @param {string} baseUrl Origin/base URL for requests.
     * @param {string} listenPath Per-session path prefix assigned during activation.
     * @param {WGSecureSession} session Authenticated secure-session state.
     */
    constructor(baseUrl, listenPath, session) {
        this.baseUrl = baseUrl.replace(/\/$/, "");
        this.listenPath = listenPath.startsWith("/")
            ? listenPath.replace(/\/$/, "")
            : "/" + listenPath.replace(/\/$/, "");
        this.session = session;
        this._preparedLogoutAuth = null;
    }

    /**
     * Build a client API from an authenticated WGAuthSession.
     * @param {Object} authSession Source containing sessionId and kSession.
     * @param {Object} [options]
     * @returns {Promise<WGClientAPI>}
     */
    static async fromAuthSession(
        authSession,
        {
            baseUrl = "",
            listenPath = "/postauth",
            secureSessionConfig = DEFAULT_SECURE_SESSION_CONFIG,
        } = {},
    ) {
        if (!authSession?.sessionId || !authSession?.kSession) {
            throw new Error("authenticated session is required");
        }

        const session = await WGSecureSession.create(
            secureSessionConfig,
            hexToBytes(authSession.kSession),
            hexToBytes(authSession.sessionId),
        );

        return new WGClientAPI(
            baseUrl,
            listenPath,
            session,
        );
    }

    /**
     * Send one authenticated JSON API request and verify its response MAC.
     *
     * apiPath is the canonical path covered by the MAC. transportPath may differ
     * when a reverse proxy requires extra escaping, but is never what gets signed.
     *
     * @param {string} method HTTP method.
     * @param {string} apiPath Canonical signed API path.
     * @param {Object|null} [object=null] JSON request body.
     * @param {string} [transportPath=apiPath] Path actually sent over HTTP.
     * @returns {Promise<{status:number, ok:boolean, data:Object|null}>}
     */
    async request(method, apiPath, object = null, transportPath = apiPath) {
        const bodyText = object === null
            ? ""
            : JSON.stringify(object);
        const body = textEncoder.encode(bodyText);

        const requestAuth = await this.session.createRequestAuth(
            method,
            apiPath,
            body,
        );

        const headers = {
            Accept: "application/json",
            "X-WG-Session-ID": requestAuth.session_id,
            "X-WG-Counter": String(requestAuth.counter),
            "X-WG-Nonce": requestAuth.nonce,
            "X-WG-MAC": requestAuth.mac,
        };

        const options = {
            method,
            headers,
        };

        if (object !== null) {
            headers["Content-Type"] = "application/json";
            options.body = bodyText;
        }

        const response = await fetch(
            this.baseUrl + this.listenPath + transportPath,
            options,
        );

        const responseBytes = new Uint8Array(
            await response.arrayBuffer(),
        );

        const responseSessionId = response.headers.get("X-WG-Session-ID");
        const responseCounter = response.headers.get("X-WG-Counter");
        const responseMac = response.headers.get("X-WG-MAC");

        if (
            responseSessionId === null
            || responseCounter === null
            || responseMac === null
        ) {
            const diagnosticText = new TextDecoder().decode(responseBytes);

            throw new Error(
                `unauthenticated response from ${apiPath}: HTTP ${response.status}`
                + (diagnosticText ? ` — ${diagnosticText}` : "")
            );
        }

        const responseAuth = {
            session_id: responseSessionId,
            counter: Number(responseCounter),
            mac: responseMac,
        };

        await this.session.verifyResponse(
            responseAuth,
            requestAuth,
            response.status,
            responseBytes,
        );

        let data = null;
        if (responseBytes.length) {
            const text = new TextDecoder().decode(responseBytes);

            try {
                data = JSON.parse(text);
            } catch {
                throw new Error(
                    `invalid JSON response from ${apiPath}: ${text}`
                );
            }
        }

        return {
            status: response.status,
            ok: response.ok,
            data,
        };
    }

    /** Read the current peer/status view. */
    status() {
        return this.request("GET", "/v1/status");
    }

    /** Send an authenticated heartbeat that refreshes auth-side idle state. */
    heartbeat() {
        return this.request("GET", "/v1/heartbeat");
    }

    /** Read merged provisioning metadata and available VPN addresses. */
    provisioning() {
        return this.request("GET", "/v1/provisioning");
    }

    /** Perform normal authenticated session logout. */
    logout() {
        this.discardPreparedLogout();
        return this.request("DELETE", "/v1/session");
    }

    /** Abandon any preallocated fast-logout request counter. */
    discardPreparedLogout() {
        if (this._preparedLogoutAuth === null) {
            return;
        }

        this.session.abandonRequest(this._preparedLogoutAuth);
        this._preparedLogoutAuth = null;
    }

    /** Preallocate authentication metadata for a keepalive-style page-unload logout. */
    async prepareFastLogout() {
        this.discardPreparedLogout();

        this._preparedLogoutAuth = await this.session.createRequestAuth(
            "DELETE",
            "/v1/session",
            new Uint8Array(0),
        );
    }

    /** Best-effort fire-and-forget logout using preallocated authentication metadata. */
    fastLogout() {
        const auth = this._preparedLogoutAuth;
        if (auth === null) {
            return false;
        }

        this._preparedLogoutAuth = null;

        const headers = {
            Accept: "application/json",
            "X-WG-Session-ID": auth.session_id,
            "X-WG-Counter": String(auth.counter),
            "X-WG-Nonce": auth.nonce,
            "X-WG-MAC": auth.mac,
        };

        try {
            fetch(
                this.baseUrl + this.listenPath + "/v1/session",
                {
                    method: "DELETE",
                    headers,
                    keepalive: true,
                },
            ).catch(() => {});
        } catch {
            return false;
        }

        return true;
    }

    /** Return canonical and Apache-safe transport paths for a WireGuard public key. */
    peerPath(publicKey) {
        const canonicalPath =
            "/v1/peers/" + encodeURIComponent(publicKey);

        // Apache rejects an encoded slash (%2F) before the request reaches
        // wg-client. Double-encode only that transport representation:
        // wg-client canonicalizes it back to the signed %2F target.
        const transportPath = canonicalPath.replace(/%2F/gi, "%252F");

        return {
            canonicalPath,
            transportPath,
        };
    }

    /** Create a peer through the authenticated client API. */
    addPeer(publicKey, allowedIp) {
        const { canonicalPath, transportPath } =
            this.peerPath(publicKey);

        return this.request(
            "PUT",
            canonicalPath,
            {
                public_key: publicKey,
                allowed_ip: allowedIp,
            },
            transportPath,
        );
    }

    /** Remove a peer through the authenticated client API. */
    removePeer(publicKey) {
        const { canonicalPath, transportPath } =
            this.peerPath(publicKey);

        return this.request(
            "DELETE",
            canonicalPath,
            null,
            transportPath,
        );
    }

    /** Read the admin-only combined runtime/ownership view. */
    adminStatus() {
        return this.request("GET", "/v1/admin/peers");
    }

    /** Reassign a live peer to another persisted user. */
    reassignOwner(publicKey, username) {
        const canonicalPath =
            "/v1/admin/peers/"
            + encodeURIComponent(publicKey)
            + "/owner";
        const transportPath =
            canonicalPath.replace(/%2F/gi, "%252F");

        return this.request(
            "PUT",
            canonicalPath,
            { username },
            transportPath,
        );
    }

    /** Create an account through the admin API. */
    createUser(username, password) {
        return this.request(
            "POST",
            "/v1/admin/users",
            {
                username,
                password,
            },
        );
    }

    /** Delete an account through the admin API. */
    deleteUser(username) {
        return this.request(
            "DELETE",
            "/v1/admin/users/" + encodeURIComponent(username),
        );
    }
}
