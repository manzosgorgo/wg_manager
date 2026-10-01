"use strict";

const fs = require("fs");
const path = require("path");

const { WGAuthHTTPClient } = require("./wg_auth_client");

function loadConfig() {
    const configPath = path.resolve(
        __dirname,
        "test_auth.conf"
    );

    const text = fs.readFileSync(configPath, "utf8");

    const config = {};
    let section = null;

    for (const rawLine of text.split(/\r?\n/)) {
        const line = rawLine.trim();

        if (!line || line.startsWith("#") || line.startsWith(";")) {
            continue;
        }

        if (line.startsWith("[") && line.endsWith("]")) {
            section = line.slice(1, -1).trim();
            config[section] ??= {};
            continue;
        }

        const separator = line.indexOf("=");

        if (separator < 0 || !section) {
            continue;
        }

        const key = line.slice(0, separator).trim();
        const value = line.slice(separator + 1).trim();

        config[section][key] = value;
    }

    return config;
}

async function main() {
    const config = loadConfig();

    const action = process.argv[2];

    if (!action) {
        throw new Error("missing action");
    }

    const username = config.auth.username;
    const password = config.auth.password;
    const serverUrl = config.server.url;

    const client = new WGAuthHTTPClient(serverUrl);

    let result;

    switch (action) {
        case "authenticate":
            result = await client.authenticate(
                username,
                password
            );
            break;

        case "status":
            result = await client.status();
            break;

        case "logout":
            result = await client.logout();
            break;

        default:
            throw new Error(`unknown action: ${action}`);
    }

    process.stdout.write(
        JSON.stringify(result) + "\n"
    );
}

main().catch((error) => {
    process.stderr.write(
        `client error: ${error.stack || error}\n`
    );

    process.exit(1);
});