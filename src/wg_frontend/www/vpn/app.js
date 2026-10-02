import { WGAuthSession } from "/js/wg_auth_session.js";
import { WGClientAPI } from "/js/wg_client_api.js";

const form = document.querySelector("#login-form");
const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const button = document.querySelector("#login-button");
const status = document.querySelector("#auth-status");
const connectionStatus = document.querySelector("#connection-status");

const auth = new WGAuthSession("");

window.wgFrontend = {
    auth,
    client: null,
};

async function refreshAuthStatus() {
    try {
        const result = await auth.status();

        if (result.ok && result.data?.ok) {
            connectionStatus.textContent = result.data.authenticated
                ? "Autenticato"
                : "Non autenticato";
        }
    } catch {
        connectionStatus.textContent = "Auth non raggiungibile";
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    button.disabled = true;
    status.className = "auth-status";
    status.textContent = "Autenticazione in corso…";

    try {
        await auth.authenticate(
            usernameInput.value,
            passwordInput.value,
        );

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

        status.className = "auth-status success";
        status.textContent =
            "Autenticazione riuscita; sessione wg-client attiva.";

        connectionStatus.textContent = "Online";

        // Keep credentials out of persistent browser storage.
        passwordInput.value = "";

    } catch (error) {
        status.className = "auth-status error";
        status.textContent = error.message ?? String(error);
        connectionStatus.textContent = "Offline";
    } finally {
        button.disabled = false;
    }
});

refreshAuthStatus();
