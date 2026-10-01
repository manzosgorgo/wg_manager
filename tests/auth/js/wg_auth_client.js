"use strict";

const https = require("https");
const fs = require("fs");

const { OpaqueClient } = require("./opaque_client");

class WGAuthHTTPClient {
    constructor(baseUrl) {
        this.baseUrl = new URL(baseUrl);
    }

    request(method, path, body = null) {
        return new Promise((resolve, reject) => {
            const payload = body === null
                ? null
                : Buffer.from(JSON.stringify(body), "utf8");

            const options = {
                hostname: this.baseUrl.hostname,
                port: this.baseUrl.port,
                path,
                method,

                // Solo per il test server locale.
                rejectUnauthorized: false,

                headers: {},
            };

            if (payload) {
                options.headers["Content-Type"] = "application/json";
                options.headers["Content-Length"] = payload.length;
            }

            const req = https.request(options, (res) => {
                const chunks = [];

                res.on("data", chunk => chunks.push(chunk));

                res.on("end", () => {
                    const raw = Buffer.concat(chunks).toString("utf8");

                    let data = null;

                    if (raw.length > 0) {
                        try {
                            data = JSON.parse(raw);
                        } catch (err) {
                            reject(new Error(
                                `invalid JSON response: ${raw}`
                            ));
                            return;
                        }
                    }

                    resolve({
                        status: res.statusCode,
                        data,
                    });
                });
            });

            req.setTimeout(10000, () => {
                req.destroy(new Error("HTTP request timeout"));
            });

            req.on("error", reject);

            if (payload) {
                req.write(payload);
            }

            req.end();
        });
    }

    async authenticate(username, password) {
        const opaqueClient = new OpaqueClient(username, password);

        /*
         * OPAQUE step 1:
         *
         * client -> server
         * username + pub
         */
        const request = await opaqueClient.start();

        const start = await this.request(
            "POST",
            "/auth",
            {
                username,
                pub: request.pub,
            }
        );

        /*
         * The state machine may reject us before OPAQUE
         * completes. This is a perfectly valid result for
         * the race tests.
         */
        if (start.status !== 200) {
            return start;
        }

        /*
         * OPAQUE step 2:
         *
         * server -> client
         *
         * Then the client computes authU.
         */
        const credentials = opaqueClient.finish(
            start.data.response
        );

        /*
         * OPAQUE verification:
         *
         * client -> server
         */
        return await this.request(
            "POST",
            "/auth/verify",
            {
                auth: credentials.auth,
            }
        );
    }

    async status() {
        return await this.request("GET", "/status");
    }

    async logout() {
        return await this.request("DELETE", "/auth");
    }
}

module.exports = {
    WGAuthHTTPClient,
};