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
const resetSessionButton = document.querySelector("#reset-session-button");

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

function showAuthView() {
    postauthView.hidden = true;
    authView.hidden = false;
    document.title = "Malandrino · Accesso";
}

function showResetSession(message = "Sessione server già attiva.") {
    status.className = "auth-status";
    status.textContent = message;
    resetSessionButton.hidden = false;
}

function hideResetSession() {
    resetSessionButton.hidden = true;
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
                showResetSession(
                    "Esiste una sessione server attiva, ma questa pagina non possiede più la chiave di sessione."
                );
            } else {
                hideResetSession();
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
        hideResetSession();

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
        showPostauthView();

    } catch (error) {
        const originalMessage = error.message ?? String(error);

        if (authenticatedHere) {
            try {
                await auth.logout();
            } catch {
                // Best-effort rollback. The original frontend error is primary.
            }

            window.wgFrontend.client = null;
        }

        status.className = "auth-status error";
        status.textContent = originalMessage;
        authConnectionStatus.textContent = "Offline";

        if (!authenticatedHere && /session already active/i.test(originalMessage)) {
            showResetSession(
                "Una sessione precedente è ancora attiva sul server."
            );
        }
    } finally {
        button.disabled = false;
    }
});

resetSessionButton.addEventListener("click", async () => {
    resetSessionButton.disabled = true;
    status.className = "auth-status";
    status.textContent = "Chiusura della sessione precedente…";

    try {
        const result = await auth.resetServerSession();

        if (!result.ok || !result.data?.ok) {
            throw new Error(
                result.data?.error
                    ?? `reset session failed (${result.status})`
            );
        }

        window.wgFrontend.client = null;
        hideResetSession();
        status.textContent = "Sessione precedente chiusa. Puoi autenticarti.";
        authConnectionStatus.textContent = "Auth online";
    } catch (error) {
        status.className = "auth-status error";
        status.textContent = error.message ?? String(error);
    } finally {
        resetSessionButton.disabled = false;
    }
});

logoutButton.addEventListener("click", async () => {
    logoutButton.disabled = true;

    try {
        await auth.logout();
    } finally {
        window.wgFrontend.client = null;
        connectionStatus.textContent = "Offline";
        showAuthView();
        logoutButton.disabled = false;
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
