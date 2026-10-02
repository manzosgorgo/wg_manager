import {
    WGSecureSession,
    hexToBytes,
} from "./wg_secure_session.js";

const textEncoder = new TextEncoder();

export const DEFAULT_SECURE_SESSION_CONFIG = {
    secure_session: {
        session_id_size: 16,
        nonce_size: 32,
        session_key_size: 32,
        counter_min: 1,
        counter_max: 4294967295,
    },
};

export class WGClientAPI {
    constructor(baseUrl, listenPath, session) {
        this.baseUrl = baseUrl.replace(/\/$/, "");
        this.listenPath = listenPath.startsWith("/")
            ? listenPath.replace(/\/$/, "")
            : "/" + listenPath.replace(/\/$/, "");
        this.session = session;
        this._preparedLogoutAuth = null;
    }

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

    async request(method, apiPath, object = null) {
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
            this.baseUrl + this.listenPath + apiPath,
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

    status() {
        return this.request("GET", "/v1/status");
    }

    heartbeat() {
        return this.request("GET", "/v1/heartbeat");
    }

    provisioning() {
        return this.request("GET", "/v1/provisioning");
    }

    logout() {
        this.discardPreparedLogout();
        return this.request("DELETE", "/v1/session");
    }

    discardPreparedLogout() {
        if (this._preparedLogoutAuth === null) {
            return;
        }

        this.session.abandonRequest(this._preparedLogoutAuth);
        this._preparedLogoutAuth = null;
    }

    async prepareFastLogout() {
        this.discardPreparedLogout();

        this._preparedLogoutAuth = await this.session.createRequestAuth(
            "DELETE",
            "/v1/session",
            new Uint8Array(0),
        );
    }

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

    addPeer(publicKey, allowedIp) {
        const path = "/v1/peers/" + encodeURIComponent(publicKey);

        return this.request(
            "PUT",
            path,
            {
                public_key: publicKey,
                allowed_ip: allowedIp,
            },
        );
    }

    removePeer(publicKey) {
        return this.request(
            "DELETE",
            "/v1/peers/" + encodeURIComponent(publicKey),
        );
    }

    adminStatus() {
        return this.request("GET", "/v1/admin/peers");
    }

    reassignOwner(publicKey, username) {
        return this.request(
            "PUT",
            "/v1/admin/peers/"
                + encodeURIComponent(publicKey)
                + "/owner",
            { username },
        );
    }

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

    deleteUser(username) {
        return this.request(
            "DELETE",
            "/v1/admin/users/" + encodeURIComponent(username),
        );
    }
}
