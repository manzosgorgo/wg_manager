function opaqueLibrary() {
    const opaque = globalThis.libopaque;

    if (!opaque) {
        throw new Error(
            "libopaque is not loaded; include /js/vendor/libopaque.js before the frontend modules"
        );
    }

    return opaque;
}

export class WGOPAQUEClient {
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
