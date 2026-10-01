"use strict";

const opaque = require("../../../vendor/libopaque/libopaque.js");

class OpaqueClient {
    constructor(username, password) {
        this.username = username;
        this.password = password;

        this.context = "wg-manager";
        this.serverId = "wg-auth";

        this.requestState = null;
    }

    async start() {
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

        const result = opaque.recoverCredentials({
            resp: opaque.hexToUint8Array(responseHex),
            sec: this.requestState.sec,
            context: this.context,
            ids: {
                idU: this.username,
                idS: this.serverId,
            },
        });

        return {
            auth: opaque.uint8ArrayToHex(result.authU),
            sessionKey: opaque.uint8ArrayToHex(result.sk),
            exportKey: opaque.uint8ArrayToHex(result.export_key),
        };
    }
}

module.exports = {
    OpaqueClient,
};