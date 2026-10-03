/**
 * Thin browser adapter around the vendored libopaque implementation.
 * Owns one OPAQUE credential request and recovers the shared session key after the server response.
 * @module wg_opaque_client
 */
function opaqueLibrary() {
    const opaque = globalThis.libopaque;

    if (!opaque) {
        throw new Error(
            "libopaque is not loaded; include /js/vendor/libopaque.js before the frontend modules"
        );
    }

    return opaque;
}

/**
 * Stateful client half of one OPAQUE authentication exchange.
 */
export class WGOPAQUEClient {
    /**
     * @param {string} username User identifier bound into the OPAQUE transcript.
     * @param {string} password User password; retained only for this exchange object.
     */
    constructor(username, password) {
        if (typeof username !== "string" || !username) {
            throw new TypeError("username must be a non-empty string");
        }
        if (typeof password !== "string" || !password) {
            throw new TypeError("password must be a non-empty string");
        }

        this.username = username;
        this.password = password;
        this.context = "wg-manager";
        this.serverId = "wg-auth";
        this.requestState = null;
    }

    /**
     * Create the OPAQUE credential request sent to POST /auth.
     * @returns {Promise<Object>} Hex-encoded public credential request.
     */
    async start() {
        const opaque = opaqueLibrary();
        await opaque.ready;

        const request = opaque.createCredentialRequest({
            pwdU: this.password,
        });

        this.requestState = request;

        return {
            pub: opaque.uint8ArrayToHex(request.pub),
        };
    }

    /**
     * Recover credentials from the server response and finish the exchange.
     * @param {string} responseHex Hex-encoded OPAQUE credential response.
     * @returns {Object}
     * @throws {Error} If start() was not called or credential recovery fails.
     */
    finish(responseHex) {
        if (!this.requestState) {
            throw new Error("OPAQUE authentication was not started");
        }

        const opaque = opaqueLibrary();
        const result = opaque.recoverCredentials({
            resp: opaque.hexToUint8Array(responseHex),
            sec: this.requestState.sec,
            context: this.context,
            ids: {
                idU: this.username,
                idS: this.serverId,
            },
        });

        this.requestState = null;

        return {
            auth: opaque.uint8ArrayToHex(result.authU),
            sessionKey: opaque.uint8ArrayToHex(result.sk),
            exportKey: opaque.uint8ArrayToHex(result.export_key),
        };
    }
}
