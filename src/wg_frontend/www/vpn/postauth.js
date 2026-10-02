import { WGAuthSession } from "/js/wg_auth_session.js";
import { WGClientAPI } from "/js/wg_client_api.js";

// Static post-auth shell.
// The real session handoff and rendering logic will be wired in the next step.
export { WGAuthSession, WGClientAPI };

const buttons = document.querySelectorAll("[data-view]");
const panels = {
    peers: document.querySelector("#view-peers"),
    "new-peer": document.querySelector("#view-new-peer"),
    admin: document.querySelector("#view-admin"),
};

for (const button of buttons) {
    button.addEventListener("click", () => {
        const selected = button.dataset.view;

        for (const [name, panel] of Object.entries(panels)) {
            panel.hidden = name !== selected;
        }
    });
}
