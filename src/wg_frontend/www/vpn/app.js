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
            await client.status();
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

function showPostauthView() {
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

        card.append(key, details);
        peerList.append(card);
    }
}

async function refreshPeers() {
    const client = window.wgFrontend.client;
    if (!client) {
        throw new Error("wg-client session is not initialized");
    }

    const result = await client.status();

    if (!result.ok || !result.data?.ok) {
        throw new Error(
            result.data?.message
                ?? result.data?.error
                ?? `wg-client returned HTTP ${result.status}`
        );
    }

    renderPeers(result);
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
    logoutButton.disabled = true;

    stopHeartbeat();

    try {
        const client = window.wgFrontend.client;
        if (client) {
            await client.logout();
        }
    } finally {
        window.wgFrontend.client = null;
        auth.clear();
        connectionStatus.textContent = "Offline";
        showAuthView();
        logoutButton.disabled = false;
        refreshAuthStatus();
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
    viewButton.addEventListener("click", () => {
        const selected = viewButton.dataset.view;

        for (const [name, panel] of Object.entries(panels)) {
            panel.hidden = name !== selected;
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
