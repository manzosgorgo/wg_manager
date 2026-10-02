# `src/wg_frontend/www/vpn/app.js`

## Metadata

- Path: `src/wg_frontend/www/vpn/app.js`
- Language: `javascript`
- Lines: 1126
- SHA256: `e67a76e4bc8188fd3e5105a145f7c469f9595604c0bd781d497506710a8c13be`
- Imports:
  - `/js/wg_auth_session.js`
  - `/js/wg_client_api.js`

## Source

```javascript
import { WGAuthSession } from "/js/wg_auth_session.js";
import { WGClientAPI } from "/js/wg_client_api.js";

const authView = document.querySelector("#auth-view");
const postauthView = document.querySelector("#postauth-view");

const form = document.querySelector("#login-form");
const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const button = document.querySelector("#login-button");
const status = document.querySelector("#auth-status");
const authConnectionStatus = document.querySelector("#auth-connection-status");

const sessionUser = document.querySelector("#session-user");
const connectionStatus = document.querySelector("#connection-status");
const logoutButton = document.querySelector("#logout-button");
const refreshPeersButton = document.querySelector("#refresh-peers");
const peerList = document.querySelector("#peer-list");
const peerStatus = document.querySelector("#peer-status");
const peerForm = document.querySelector("#peer-form");
const peerPublicKeyInput = document.querySelector("#peer-public-key");
const peerGenerateKeysButton = document.querySelector("#peer-generate-keys");
const peerCreateButton = document.querySelector("#peer-create-button");
const peerAllowedIpInput = document.querySelector("#peer-allowed-ip");
const peerRoutingModeInput = document.querySelector("#peer-routing-mode");
const peerKeepaliveInput = document.querySelector("#peer-keepalive");
const peerConfigPanel = document.querySelector("#peer-config-panel");
const peerConfigPreview = document.querySelector("#peer-config-preview");
const peerDownloadConfigButton = document.querySelector("#peer-download-config");
const peerNewProvisioningButton = document.querySelector("#peer-new-provisioning");
const peerQrPanel = document.querySelector("#peer-qr-panel");
const peerQrScannedButton = document.querySelector("#peer-qr-scanned");
const peerQrStatus = document.querySelector("#peer-qr-status");
const peerQrCode = document.querySelector("#peer-qr-code");
const peerCreateStatus = document.querySelector("#peer-create-status");
const provisioningDebug = document.querySelector("#provisioning-debug");

let provisioningState = null;
let generatedKeyPair = null;
let provisionedPeer = false;
let configPendingExport = false;

function setConfigPendingExport(pending) {
    configPendingExport = Boolean(pending);
}

function confirmDiscardPendingConfig(message) {
    if (!configPendingExport) {
        return true;
    }

    return window.confirm(
        message
        ?? "La configurazione contiene una private key che non è ancora stata salvata. Continuando verrà persa. Procedere?"
    );
}

window.addEventListener("beforeunload", (event) => {
    if (!configPendingExport) {
        return;
    }

    event.preventDefault();
    event.returnValue = "";
});

const adminNavButton = document.querySelector("#admin-nav-button");
const adminPeerList = document.querySelector("#admin-peer-list");
const adminUserList = document.querySelector("#admin-user-list");
const adminStatus = document.querySelector("#admin-status");
const userForm = document.querySelector("#user-form");
const newUsernameInput = document.querySelector("#new-username");
const newPasswordInput = document.querySelector("#new-password");

const auth = new WGAuthSession("");

window.wgFrontend = {
    auth,
    client: null,
};

const HEARTBEAT_INTERVAL_MS = 10_000;
let heartbeatTimer = null;

function stopHeartbeat() {
    if (heartbeatTimer !== null) {
        clearInterval(heartbeatTimer);
        heartbeatTimer = null;
    }
}

function startHeartbeat() {
    stopHeartbeat();

    heartbeatTimer = setInterval(async () => {
        const client = window.wgFrontend.client;
        if (!client) {
            stopHeartbeat();
            return;
        }

        try {
            const heartbeat = await client.heartbeat();

            if (!heartbeat.ok || !heartbeat.data?.ok) {
                throw new Error(
                    heartbeat.data?.message
                        ?? heartbeat.data?.error
                        ?? `wg-client heartbeat returned HTTP ${heartbeat.status}`
                );
            }

            await client.prepareFastLogout();
        } catch (error) {
            stopHeartbeat();
            window.wgFrontend.client = null;
            connectionStatus.textContent = "Sessione persa";
            showAuthView();
            status.className = "auth-status error";
            status.textContent =
                error.message ?? "La sessione non è più raggiungibile.";
            refreshAuthStatus();
        }
    }, HEARTBEAT_INTERVAL_MS);
}

function showAuthView() {
    postauthView.hidden = true;
    authView.hidden = false;
    document.title = "Malandrino · Accesso";
}

function showPeerView() {
    for (const [name, panel] of Object.entries(panels)) {
        panel.hidden = name !== "peers";
    }
}

function showPostauthView() {
    showPeerView();
    authView.hidden = true;
    postauthView.hidden = false;
    sessionUser.textContent = auth.username ?? "";
    connectionStatus.textContent = "Online";
    document.title = "Malandrino · WireGuard";
}

function renderPeers(result) {
    const peers = result?.data?.peers;

    if (!Array.isArray(peers) || peers.length === 0) {
        peerList.innerHTML = [
            '<article class="placeholder-card">',
            "<strong>Nessun peer</strong>",
            "<span>Non risultano peer associati a questa sessione.</span>",
            "</article>",
        ].join("");
        return;
    }

    peerList.innerHTML = "";

    for (const peer of peers) {
        const card = document.createElement("article");
        card.className = "placeholder-card";

        const key = document.createElement("strong");
        key.textContent = peer.public_key ?? "peer senza public key";

        const details = document.createElement("span");
        const allowed = Array.isArray(peer.allowed_ips)
            ? peer.allowed_ips.join(", ")
            : "";
        details.textContent = allowed || "Nessun allowed IP";

        const actions = document.createElement("div");
        actions.className = "card-actions";

        const regenerateButton = document.createElement("button");
        regenerateButton.type = "button";
        regenerateButton.textContent = "Rigenera configurazione";
        regenerateButton.addEventListener("click", async () => {
            const publicKey = peer.public_key;
            const allowedIp = Array.isArray(peer.allowed_ips)
                ? peer.allowed_ips[0]
                : peer.allowed_ip;

            if (!publicKey || !allowedIp) {
                peerStatus.className = "operation-status error";
                peerStatus.textContent =
                    "Il peer non contiene public key e allowed IP sufficienti per la rigenerazione.";
                return;
            }

            const confirmed = window.confirm(
                "Rigenerare la configurazione di questo peer?\n\n"
                + "Verrà generata una nuova coppia di chiavi e il peer attuale verrà sostituito. "
                + "La configurazione WireGuard già installata sul dispositivo non funzionerà più "
                + "e dovrà essere sostituita con quella nuova."
            );

            if (!confirmed) {
                return;
            }

            regenerateButton.disabled = true;
            removeButton.disabled = true;
            peerStatus.className = "operation-status";
            peerStatus.textContent = "Rigenerazione peer in corso…";

            let oldPeerRemoved = false;

            try {
                const client = window.wgFrontend.client;
                if (!client) {
                    throw new Error("wg-client session is not initialized");
                }

                const provisioningResult = await client.provisioning();
                if (!provisioningResult.ok) {
                    throw new Error(
                        provisioningResult.data?.message
                            ?? provisioningResult.data?.error
                            ?? `wg-client returned HTTP ${provisioningResult.status}`
                    );
                }

                provisioningState = provisioningResult.data ?? {};

                provisioningDebug.textContent = [
                    `interface: ${provisioningState.interface ?? "?"}`,
                    `vpn_network: ${provisioningState.vpn_network ?? "?"}`,
                    `server_address: ${provisioningState.server_address ?? "(non configurato)"}`,
                    `server_public_key: ${provisioningState.server_public_key ?? "?"}`,
                    `listen_port: ${provisioningState.listen_port ?? "?"}`,
                    `endpoint: ${provisioningState.endpoint ?? "(non configurato)"}`,
                    `used_ips: ${Array.isArray(provisioningState.used_ips) ? provisioningState.used_ips.join(", ") : ""}`,
                    `reserved_ips: ${Array.isArray(provisioningState.reserved_ips) ? provisioningState.reserved_ips.join(", ") : ""}`,
                    `available_ips: ${Array.isArray(provisioningState.available_ips) ? provisioningState.available_ips.join(", ") : ""}`,
                ].join("\n");

                const newKeyPair = await generateWireGuardKeyPair();

                const removeResult = await client.removePeer(publicKey);
                if (!removeResult.ok) {
                    throw new Error(
                        removeResult.data?.message
                            ?? removeResult.data?.error
                            ?? `wg-client returned HTTP ${removeResult.status}`
                    );
                }
                oldPeerRemoved = true;

                const addResult = await client.addPeer(
                    newKeyPair.publicKey,
                    allowedIp,
                );

                if (!addResult.ok) {
                    throw new Error(
                        addResult.data?.message
                            ?? addResult.data?.error
                            ?? `wg-client returned HTTP ${addResult.status}`
                    );
                }

                generatedKeyPair = newKeyPair;
                provisionedPeer = true;
                setConfigPendingExport(true);
                peerConfigPanel.hidden = false;
                peerDownloadConfigButton.hidden = false;
                peerQrPanel.hidden = false;

                peerPublicKeyInput.value = newKeyPair.publicKey;

                const existingOption = Array.from(peerAllowedIpInput.options)
                    .find((option) => option.value === allowedIp);

                if (existingOption) {
                    peerAllowedIpInput.value = allowedIp;
                } else {
                    const option = document.createElement("option");
                    option.value = allowedIp;
                    option.textContent = allowedIp;
                    option.selected = true;
                    peerAllowedIpInput.append(option);
                }

                peerPublicKeyInput.disabled = true;
                peerAllowedIpInput.disabled = true;
                peerRoutingModeInput.disabled = true;
                peerKeepaliveInput.disabled = true;
                peerGenerateKeysButton.disabled = true;
                peerCreateButton.disabled = true;
                peerNewProvisioningButton.hidden = false;

                peerQrCode.replaceChildren();
                peerQrCode.hidden = true;
                peerQrScannedButton.hidden = true;

                renderClientConfigPreview();

                for (const [name, panel] of Object.entries(panels)) {
                    panel.hidden = name !== "new-peer";
                }

                renderQrCode();
                await refreshPeers();

                peerCreateStatus.className = "operation-status success";
                peerCreateStatus.textContent =
                    "Peer rigenerato. Scarica la nuova configurazione o acquisisci il QR.";
                peerStatus.className = "operation-status success";
                peerStatus.textContent =
                    "Configurazione rigenerata: quella precedente non è più valida.";

            } catch (error) {
                peerStatus.className = "operation-status error";
                peerStatus.textContent = oldPeerRemoved
                    ? `Rigenerazione fallita dopo la rimozione del vecchio peer: ${error.message ?? String(error)}`
                    : (error.message ?? String(error));
                regenerateButton.disabled = false;
                removeButton.disabled = false;
            }
        });

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "Elimina";
        removeButton.addEventListener("click", async () => {
            const publicKey = peer.public_key;

            if (!publicKey) {
                return;
            }

            if (!window.confirm("Eliminare questo peer?")) {
                return;
            }

            removeButton.disabled = true;
            peerStatus.className = "operation-status";
            peerStatus.textContent = "Eliminazione peer in corso…";

            try {
                const client = window.wgFrontend.client;
                const result = await client.removePeer(publicKey);

                if (!result.ok) {
                    throw new Error(
                        result.data?.message
                            ?? result.data?.error
                            ?? `wg-client returned HTTP ${result.status}`
                    );
                }

                await refreshPeers();
                peerStatus.className = "operation-status success";
                peerStatus.textContent = "Peer eliminato.";

            } catch (error) {
                peerStatus.className = "operation-status error";
                peerStatus.textContent = error.message ?? String(error);
                removeButton.disabled = false;
            }
        });

        actions.append(regenerateButton, removeButton);
        card.append(key, details, actions);
        peerList.append(card);
    }
}

function clientAllowedIpsForMode(data, mode) {
    if (mode === "full") {
        return ["0.0.0.0/0", "::/0"];
    }

    return data?.vpn_network
        ? [data.vpn_network]
        : [];
}

function base64UrlToWireGuard(value) {
    const normalized = value
        .replace(/-/g, "+")
        .replace(/_/g, "/");
    const padding = "=".repeat((4 - normalized.length % 4) % 4);
    return normalized + padding;
}

async function generateWireGuardKeyPair() {
    const keyPair = await crypto.subtle.generateKey(
        { name: "X25519" },
        true,
        ["deriveBits"],
    );

    const [privateJwk, publicJwk] = await Promise.all([
        crypto.subtle.exportKey("jwk", keyPair.privateKey),
        crypto.subtle.exportKey("jwk", keyPair.publicKey),
    ]);

    if (
        privateJwk.crv !== "X25519"
        || publicJwk.crv !== "X25519"
        || typeof privateJwk.d !== "string"
        || typeof publicJwk.x !== "string"
    ) {
        throw new Error("browser returned an invalid X25519 key pair");
    }

    return {
        privateKey: base64UrlToWireGuard(privateJwk.d),
        publicKey: base64UrlToWireGuard(publicJwk.x),
    };
}

function configIsComplete(text) {
    return (
        typeof text === "string"
        && text.length > 0
        && !text.includes("<")
        && !text.includes(">")
    );
}

function updateQrAvailability() {
    const configText = peerConfigPreview.textContent ?? "";
    const ready = provisionedPeer && configIsComplete(configText);

    peerDownloadConfigButton.disabled = !ready;
    peerQrStatus.textContent = ready
        ? "Configurazione completa: QR pronto per l'importazione."
        : "Il QR sarà disponibile quando la configurazione sarà completa.";

    if (!ready) {
        peerQrCode.replaceChildren();
        peerQrCode.hidden = true;
        peerQrScannedButton.hidden = true;
    }
}

function renderClientConfigPreview() {
    const data = provisioningState ?? {};
    const address = peerAllowedIpInput.value;
    const routingMode = peerRoutingModeInput.value;
    const keepalive = Number(peerKeepaliveInput.value);

    if (!provisionedPeer || !generatedKeyPair || !address) {
        peerConfigPreview.textContent = "";
        updateQrAvailability();
        return;
    }

    const allowedIps = clientAllowedIpsForMode(
        data,
        routingMode,
    );

    peerConfigPreview.textContent = [
        "[Interface]",
        `PrivateKey = ${generatedKeyPair.privateKey}`,
        `Address = ${address}`,
        "",
        "[Peer]",
        `PublicKey = ${data.server_public_key ?? "<server public key>"}`,
        `Endpoint = ${data.endpoint ?? "<server endpoint>"}`,
        `AllowedIPs = ${allowedIps.join(", ")}`,
        ...(keepalive > 0
            ? [`PersistentKeepalive = ${keepalive}`]
            : []),
    ].join("\n");

    updateQrAvailability();
}

async function refreshProvisioning() {
    const client = window.wgFrontend.client;
    if (!client) {
        throw new Error("wg-client session is not initialized");
    }

    provisioningDebug.textContent = "Caricamento…";

    const result = await client.provisioning();

    if (!result.ok) {
        throw new Error(
            result.data?.message
                ?? result.data?.error
                ?? `wg-client returned HTTP ${result.status}`
        );
    }

    const data = result.data ?? {};
    provisioningState = data;

    const availableIps = Array.isArray(data.available_ips)
        ? data.available_ips
        : [];

    peerAllowedIpInput.innerHTML = "";

    if (availableIps.length === 0) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Nessun IP disponibile";
        peerAllowedIpInput.append(option);
        peerAllowedIpInput.disabled = true;
    } else {
        peerAllowedIpInput.disabled = false;

        for (const ip of availableIps) {
            const option = document.createElement("option");
            option.value = ip;
            option.textContent = ip;
            peerAllowedIpInput.append(option);
        }
    }

    renderClientConfigPreview();

    provisioningDebug.textContent = [
        `interface: ${data.interface ?? "?"}`,
        `vpn_network: ${data.vpn_network ?? "?"}`,
        `server_address: ${data.server_address ?? "(non configurato)"}`,
        `server_public_key: ${data.server_public_key ?? "?"}`,
        `listen_port: ${data.listen_port ?? "?"}`,
        `endpoint: ${data.endpoint ?? "(non configurato)"}`,
        `used_ips: ${Array.isArray(data.used_ips) ? data.used_ips.join(", ") : ""}`,
        `reserved_ips: ${Array.isArray(data.reserved_ips) ? data.reserved_ips.join(", ") : ""}`,
        `available_ips: ${Array.isArray(data.available_ips) ? data.available_ips.join(", ") : ""}`,
    ].join("\n");

    return result;
}


async function refreshPeers() {
    const client = window.wgFrontend.client;
    if (!client) {
        throw new Error("wg-client session is not initialized");
    }

    const result = await client.status();

    if (!result.ok) {
        throw new Error(
            result.data?.message
                ?? result.data?.error
                ?? `wg-client returned HTTP ${result.status}`
        );
    }

    renderPeers(result);
    return result;
}


function renderAdminState(result) {
    const data = result?.data ?? {};
    const users = Array.isArray(data.users) ? data.users : [];
    const peers = Array.isArray(data.peers) ? data.peers : [];

    adminPeerList.innerHTML = "";
    adminUserList.innerHTML = "";

    if (peers.length === 0) {
        adminPeerList.innerHTML =
            '<article class="placeholder-card"><strong>Nessun peer</strong><span>Nessun record ownership disponibile.</span></article>';
    } else {
        for (const peer of peers) {
            const card = document.createElement("article");
            card.className = "placeholder-card";

            const key = document.createElement("strong");
            key.textContent = peer.public_key ?? "peer senza public key";

            const details = document.createElement("span");
            details.textContent =
                `owner: ${peer.owner ?? "nessuno"} · ip: ${peer.allowed_ip ?? "?"} · stato: ${peer.ownership_state ?? "?"}`;

            const form = document.createElement("form");
            form.className = "inline-admin-form";

            const select = document.createElement("select");
            for (const username of users) {
                const option = document.createElement("option");
                option.value = username;
                option.textContent = username;
                option.selected = username === peer.owner;
                select.append(option);
            }

            const button = document.createElement("button");
            button.type = "submit";
            button.textContent = "Assegna owner";

            form.addEventListener("submit", async (event) => {
                event.preventDefault();
                button.disabled = true;

                try {
                    const result = await window.wgFrontend.client.reassignOwner(
                        peer.public_key,
                        select.value,
                    );

                    if (!result.ok) {
                        throw new Error(
                            result.data?.message
                                ?? result.data?.error
                                ?? `wg-client returned HTTP ${result.status}`
                        );
                    }

                    await refreshAdmin();
                    adminStatus.className = "operation-status success";
                    adminStatus.textContent = "Ownership aggiornata.";

                } catch (error) {
                    adminStatus.className = "operation-status error";
                    adminStatus.textContent = error.message ?? String(error);
                    button.disabled = false;
                }
            });

            form.append(select, button);
            card.append(key, details, form);
            adminPeerList.append(card);
        }
    }

    if (users.length === 0) {
        adminUserList.innerHTML =
            '<article class="placeholder-card"><strong>Nessun utente</strong></article>';
    } else {
        for (const username of users) {
            const card = document.createElement("article");
            card.className = "placeholder-card";

            const name = document.createElement("strong");
            name.textContent = username;

            const actions = document.createElement("div");
            actions.className = "card-actions";

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.textContent = "Elimina";
            removeButton.disabled = username === auth.username;

            removeButton.addEventListener("click", async () => {
                if (!window.confirm(`Eliminare l'utente ${username}?`)) {
                    return;
                }

                removeButton.disabled = true;

                try {
                    const result = await window.wgFrontend.client.deleteUser(username);

                    if (!result.ok) {
                        throw new Error(
                            result.data?.message
                                ?? result.data?.error
                                ?? `wg-client returned HTTP ${result.status}`
                        );
                    }

                    await refreshAdmin();
                    adminStatus.className = "operation-status success";
                    adminStatus.textContent = "Utente eliminato.";

                } catch (error) {
                    adminStatus.className = "operation-status error";
                    adminStatus.textContent = error.message ?? String(error);
                    removeButton.disabled = false;
                }
            });

            actions.append(removeButton);
            card.append(name, actions);
            adminUserList.append(card);
        }
    }
}

async function refreshAdmin() {
    const client = window.wgFrontend.client;
    if (!client) {
        throw new Error("wg-client session is not initialized");
    }

    const result = await client.adminStatus();

    if (!result.ok) {
        throw new Error(
            result.data?.message
                ?? result.data?.error
                ?? `wg-client returned HTTP ${result.status}`
        );
    }

    renderAdminState(result);
    return result;
}


async function refreshAuthStatus() {
    try {
        const result = await auth.status();

        if (result.ok && result.data?.ok) {
            const serverSessionActive =
                result.data.authenticated || result.data.client_active;

            authConnectionStatus.textContent = serverSessionActive
                ? "Sessione auth già attiva"
                : "Auth online";

            if (serverSessionActive && !auth.sessionId) {
                status.className = "auth-status";
                status.textContent =
                    "Esiste una sessione server ancora attiva. Verrà chiusa automaticamente se il browser che la possiede non invia più richieste autenticate.";
            }
        }
    } catch {
        authConnectionStatus.textContent = "Auth non raggiungibile";
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    button.disabled = true;
    status.className = "auth-status";
    status.textContent = "Autenticazione in corso…";

    let authenticatedHere = false;

    try {
        await auth.authenticate(
            usernameInput.value,
            passwordInput.value,
        );
        authenticatedHere = true;

        const client = await WGClientAPI.fromAuthSession(auth);
        window.wgFrontend.client = client;

        const clientStatus = await client.status();

        if (!clientStatus.ok || !clientStatus.data?.ok) {
            throw new Error(
                clientStatus.data?.message
                    ?? clientStatus.data?.error
                    ?? `wg-client returned HTTP ${clientStatus.status}`
            );
        }

        passwordInput.value = "";
        renderPeers(clientStatus);

        const isAdmin = auth.username === "admin";
        adminNavButton.hidden = !isAdmin;

        if (isAdmin) {
            try {
                await refreshAdmin();
            } catch (error) {
                adminStatus.className = "operation-status error";
                adminStatus.textContent = error.message ?? String(error);
            }
        }
        await client.prepareFastLogout();
        showPostauthView();
        startHeartbeat();

    } catch (error) {
        const originalMessage = error.message ?? String(error);

        if (authenticatedHere) {
            stopHeartbeat();

            const client = window.wgFrontend.client;
            if (client) {
                try {
                    await client.logout();
                } catch {
                    // The idle timeout remains the fallback recovery path.
                }
            }

            window.wgFrontend.client = null;
            auth.clear();
        }

        status.className = "auth-status error";
        status.textContent = originalMessage;
        authConnectionStatus.textContent = "Offline";

    } finally {
        button.disabled = false;
    }
});

logoutButton.addEventListener("click", async () => {
    if (!confirmDiscardPendingConfig(
        "La nuova configurazione non è ancora stata salvata. Uscendo ora la private key verrà persa. Effettuare comunque il logout?"
    )) {
        return;
    }

    logoutButton.disabled = true;
    setConfigPendingExport(false);

    stopHeartbeat();

    try {
        const client = window.wgFrontend.client;
        if (client) {
            await client.logout();
        }
    } finally {
        window.wgFrontend.client = null;
        generatedKeyPair = null;
        provisionedPeer = false;
        auth.clear();
        connectionStatus.textContent = "Offline";
        showAuthView();
        logoutButton.disabled = false;
        refreshAuthStatus();
    }
});

peerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const client = window.wgFrontend.client;
    if (!client) {
        return;
    }

    const publicKey = peerPublicKeyInput.value.trim();
    const allowedIp = peerAllowedIpInput.value.trim();
    const submitButton = peerCreateButton;

    if (!generatedKeyPair || !publicKey) {
        peerCreateStatus.className = "operation-status error";
        peerCreateStatus.textContent = "Genera prima una coppia di chiavi.";
        return;
    }

    submitButton.disabled = true;
    peerCreateStatus.className = "operation-status";
    peerCreateStatus.textContent = "Creazione peer in corso…";

    try {
        const result = await client.addPeer(publicKey, allowedIp);

        if (!result.ok) {
            throw new Error(
                result.data?.message
                    ?? result.data?.error
                    ?? `wg-client returned HTTP ${result.status}`
            );
        }

        provisionedPeer = true;
        peerConfigPanel.hidden = false;
        peerDownloadConfigButton.hidden = false;
        peerQrPanel.hidden = false;

        peerPublicKeyInput.disabled = true;
        peerAllowedIpInput.disabled = true;
        peerRoutingModeInput.disabled = true;
        peerKeepaliveInput.disabled = true;
        peerGenerateKeysButton.disabled = true;
        peerCreateButton.disabled = true;
        peerNewProvisioningButton.hidden = false;

        renderClientConfigPreview();
        renderQrCode();
        await refreshPeers();

        peerCreateStatus.className = "operation-status success";
        peerCreateStatus.textContent =
            "Peer creato. Scarica ora la configurazione o acquisisci il QR.";

    } catch (error) {
        peerCreateStatus.className = "operation-status error";
        peerCreateStatus.textContent = error.message ?? String(error);
    } finally {
        if (!provisionedPeer) {
            submitButton.disabled = false;
        }
    }
});

peerGenerateKeysButton.addEventListener("click", async () => {
    peerGenerateKeysButton.disabled = true;
    peerCreateStatus.className = "operation-status";
    peerCreateStatus.textContent = "Generazione chiavi X25519…";

    try {
        generatedKeyPair = await generateWireGuardKeyPair();
        setConfigPendingExport(true);
        peerPublicKeyInput.value = generatedKeyPair.publicKey;
        renderClientConfigPreview();

        peerCreateStatus.className = "operation-status success";
        peerCreateStatus.textContent =
            "Chiavi generate nel browser. La private key non verrà inviata al server.";
        peerGenerateKeysButton.disabled = false;
    } catch (error) {
        generatedKeyPair = null;
        peerPublicKeyInput.value = "";
        peerCreateStatus.className = "operation-status error";
        peerCreateStatus.textContent =
            error.message ?? "Generazione X25519 non supportata dal browser.";
        peerGenerateKeysButton.disabled = false;
    }
});

peerDownloadConfigButton.addEventListener("click", () => {
    const configText = peerConfigPreview.textContent ?? "";

    if (!provisionedPeer || !configIsComplete(configText)) {
        updateQrAvailability();
        return;
    }

    const blob = new Blob(
        [configText + "\n"],
        { type: "text/plain;charset=utf-8" },
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "wg-client.conf";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);

    setConfigPendingExport(false);
    peerQrStatus.textContent =
        "Configurazione scaricata. La protezione contro la chiusura è stata disattivata.";
});

peerNewProvisioningButton.addEventListener("click", async () => {
    if (!confirmDiscardPendingConfig(
        "La configurazione corrente non è ancora stata salvata. Preparando un altro peer la private key verrà persa. Continuare?"
    )) {
        return;
    }

    setConfigPendingExport(false);
    generatedKeyPair = null;
    provisionedPeer = false;

    peerForm.reset();
    peerPublicKeyInput.value = "";
    peerPublicKeyInput.disabled = false;
    peerAllowedIpInput.disabled = false;
    peerRoutingModeInput.disabled = false;
    peerKeepaliveInput.disabled = false;
    peerGenerateKeysButton.disabled = false;
    peerCreateButton.disabled = false;
    peerNewProvisioningButton.hidden = true;
    peerConfigPanel.hidden = true;
    peerDownloadConfigButton.hidden = true;
    peerQrPanel.hidden = true;

    peerQrCode.replaceChildren();
    peerQrCode.hidden = true;
    peerQrScannedButton.hidden = true;
    peerCreateStatus.className = "operation-status";
    peerCreateStatus.textContent = "";

    await refreshProvisioning();
    renderClientConfigPreview();
});

function renderQrCode() {
    const configText = peerConfigPreview.textContent ?? "";

    if (!provisionedPeer || !configIsComplete(configText)) {
        updateQrAvailability();
        return;
    }

    peerQrCode.replaceChildren();
    peerQrCode.hidden = false;

    new window.QRCode(peerQrCode, {
        text: configText,
        width: 280,
        height: 280,
        correctLevel: window.QRCode.CorrectLevel.M,
    });

    peerQrScannedButton.hidden = false;
    peerQrStatus.textContent =
        "QR pronto per l'importazione.";
}

peerQrScannedButton.addEventListener("click", () => {
    setConfigPendingExport(false);
    peerQrScannedButton.hidden = true;
    peerQrStatus.textContent =
        "QR acquisito. La protezione contro la chiusura è stata disattivata.";
});

peerAllowedIpInput.addEventListener("change", renderClientConfigPreview);
peerRoutingModeInput.addEventListener("change", renderClientConfigPreview);
peerKeepaliveInput.addEventListener("change", renderClientConfigPreview);

userForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const client = window.wgFrontend.client;
    if (!client) {
        return;
    }

    const username = newUsernameInput.value.trim();
    const password = newPasswordInput.value;
    const submitButton = userForm.querySelector('button[type="submit"]');

    submitButton.disabled = true;
    adminStatus.className = "operation-status";
    adminStatus.textContent = "Creazione utente in corso…";

    try {
        const result = await client.createUser(username, password);

        if (!result.ok) {
            throw new Error(
                result.data?.message
                    ?? result.data?.error
                    ?? `wg-client returned HTTP ${result.status}`
            );
        }

        userForm.reset();
        await refreshAdmin();

        adminStatus.className = "operation-status success";
        adminStatus.textContent = "Utente creato.";

    } catch (error) {
        adminStatus.className = "operation-status error";
        adminStatus.textContent = error.message ?? String(error);
    } finally {
        submitButton.disabled = false;
    }
});

refreshPeersButton.addEventListener("click", async () => {
    refreshPeersButton.disabled = true;

    try {
        await refreshPeers();
        connectionStatus.textContent = "Online";
    } catch (error) {
        connectionStatus.textContent =
            error.message ?? String(error);
    } finally {
        refreshPeersButton.disabled = false;
    }
});

const viewButtons = document.querySelectorAll("[data-view]");
const panels = {
    peers: document.querySelector("#view-peers"),
    "new-peer": document.querySelector("#view-new-peer"),
    admin: document.querySelector("#view-admin"),
};

for (const viewButton of viewButtons) {
    viewButton.addEventListener("click", async () => {
        const selected = viewButton.dataset.view;

        for (const [name, panel] of Object.entries(panels)) {
            panel.hidden = name !== selected;
        }

        if (selected === "new-peer") {
            try {
                await refreshProvisioning();
            } catch (error) {
                provisioningDebug.textContent =
                    error.message ?? String(error);
            }
        }

        if (selected === "admin" && !adminNavButton.hidden) {
            try {
                await refreshAdmin();
            } catch (error) {
                adminStatus.className = "operation-status error";
                adminStatus.textContent = error.message ?? String(error);
            }
        }
    });
}

showAuthView();
refreshAuthStatus();


window.addEventListener("pagehide", (event) => {
    if (event.persisted) {
        return;
    }

    stopHeartbeat();

    const client = window.wgFrontend.client;
    if (client) {
        client.fastLogout();
    }
});
```
