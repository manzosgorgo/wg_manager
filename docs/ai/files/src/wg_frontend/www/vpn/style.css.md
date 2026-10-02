# `src/wg_frontend/www/vpn/style.css`

## Metadata

- Path: `src/wg_frontend/www/vpn/style.css`
- Language: `css`
- Lines: 549
- SHA256: `570744543a10a2fdfb2c5ec7c87a1b144baa5253801c539892ad69933490a3a1`

## Source

```css
[hidden] {
  display: none !important;
}

/* ============================================================
   Authentication
   ============================================================ */
:root {
  color-scheme: dark;
  --bg: #0a0d12;
  --panel: #11161e;
  --panel-hover: #171e28;
  --border: #202936;
  --text: #edf2f7;
  --muted: #8995a5;
  --accent: #70a7ff;
  --online: #57d18c;
  --offline: #e56b78;
  --unknown: #d5a84f;
}

* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; }
body {
  background: radial-gradient(circle at 20% -10%, #172131 0, var(--bg) 38%);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}


.auth-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.auth-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;

  padding: 70px 0;
}

.auth-card {
  width: min(420px, 100%);

  border: 1px solid var(--border);
  background:
    linear-gradient(
      145deg,
      rgba(19,25,34,.97),
      rgba(13,17,23,.97)
    );

  border-radius: 18px;
  padding: 30px;

  box-shadow:
    0 20px 60px rgba(0,0,0,.25);
}

.auth-icon {
  width: 46px;
  height: 46px;

  display: flex;
  align-items: center;
  justify-content: center;

  border: 1px solid var(--border);
  border-radius: 12px;

  background: rgba(17,22,30,.8);

  font-size: 21px;

  margin-bottom: 24px;
}

.auth-heading .eyebrow {
  margin-bottom: 8px;
}

.auth-heading h2 {
  margin: 0;

  font-size: 27px;
  line-height: 1.1;
  letter-spacing: -.025em;
}

.auth-heading p {
  margin: 11px 0 27px;

  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}


.auth-label {
  display: block;

  margin-bottom: 8px;

  color: #b9c3d0;

  font-size: 12px;
  font-weight: 700;
}


.auth-card input[type="text"],
.auth-card input[type="password"] {
  width: 100%;

  border: 1px solid var(--border);
  outline: 0;

  background: rgba(17,22,30,.75);
  color: var(--text);

  border-radius: 10px;

  padding: 12px 13px;

  font: inherit;
  font-size: 14px;

  transition:
    border-color .16s ease,
    background .16s ease,
    box-shadow .16s ease;
}

.auth-card input[type="text"]:hover,
.auth-card input[type="password"]:hover {
  border-color: #334154;
}

.auth-card input[type="text"]:focus,
.auth-card input[type="password"]:focus {
  border-color: var(--accent);

  background: rgba(17,22,30,.95);

  box-shadow:
    0 0 0 3px rgba(112,167,255,.10);
}


.auth-button {
  width: 100%;

  margin-top: 14px;

  border: 1px solid var(--accent);
  border-radius: 10px;

  background: rgba(112,167,255,.12);
  color: var(--text);

  padding: 11px 14px;

  cursor: pointer;

  font: inherit;
  font-size: 13px;
  font-weight: 700;

  transition:
    background .16s ease,
    border-color .16s ease,
    transform .16s ease;
}

.auth-button:hover {
  background: rgba(112,167,255,.20);
  transform: translateY(-1px);
}

.auth-button:active {
  transform: translateY(0);
}

.auth-button:disabled {
  opacity: .55;
  cursor: wait;
  transform: none;
}


.auth-status {
  min-height: 18px;

  margin-top: 15px;

  color: var(--muted);

  font-size: 11px;
  line-height: 1.5;

  text-align: center;
}

.auth-status.error {
  color: var(--offline);
}

.auth-status.success {
  color: var(--online);
}


@media (max-width: 600px) {

  .auth-main {
    align-items: flex-start;

    padding-top: 45px;
  }

  .auth-card {
    padding: 24px;
  }

}


/* ============================================================
   Post-auth shell
   ============================================================ */

.postauth-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.postauth-header,
.postauth-main,
.postauth-shell footer {
  width: min(1180px, calc(100% - 40px));
  margin-left: auto;
  margin-right: auto;
}

.postauth-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 0 18px;
}

.postauth-header h1,
.section-heading h2,
.postauth-panel h3 {
  margin: 0;
}

.session-actions,
.section-heading,
.postauth-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.postauth-main {
  flex: 1;
  padding: 18px 0 40px;
}

.postauth-nav {
  margin-bottom: 18px;
}

.postauth-nav button,
.session-actions button,
.section-heading button,
.postauth-form button {
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--panel);
  color: var(--text);
  padding: 9px 13px;
  cursor: pointer;
}

.postauth-panel {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(17, 22, 30, .9);
  padding: 24px;
}

.section-heading {
  justify-content: space-between;
  margin-bottom: 20px;
}

.placeholder-list,
.admin-grid {
  display: grid;
  gap: 14px;
}

.admin-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.placeholder-card {
  border: 1px dashed var(--border);
  border-radius: 12px;
  padding: 18px;
  color: var(--muted);
}

.placeholder-card strong,
.placeholder-card span {
  display: block;
}

.placeholder-card strong {
  color: var(--text);
  margin-bottom: 6px;
}

.postauth-form {
  display: grid;
  gap: 14px;
  margin-bottom: 18px;
}

.postauth-form label {
  display: grid;
  gap: 7px;
  color: #b9c3d0;
  font-size: 12px;
  font-weight: 700;
}

.postauth-form input,
.postauth-form select {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(17, 22, 30, .75);
  color: var(--text);
  padding: 11px 12px;
  font: inherit;
}

.placeholder-card pre {
  margin: 10px 0 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: #b9c3d0;
  font: 12px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.postauth-shell footer {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 0 26px;
  color: var(--muted);
  font-size: 11px;
}

@media (max-width: 760px) {
  .postauth-header,
  .section-heading,
  .postauth-shell footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-grid {
    grid-template-columns: 1fr;
  }

  .postauth-nav {
    flex-wrap: wrap;
  }
}

.auth-card input + .auth-label {
  margin-top: 14px;
}


.operation-status {
  min-height: 18px;
  margin-top: 12px;
  color: var(--muted);
  font-size: 12px;
}

.operation-status.success {
  color: var(--online);
}

.operation-status.error {
  color: var(--offline);
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.card-actions button {
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--panel);
  color: var(--text);
  padding: 8px 12px;
  cursor: pointer;
}

.card-actions button:disabled {
  opacity: .55;
  cursor: wait;
}


.inline-admin-form {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.inline-admin-form select {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--panel);
  color: var(--text);
  padding: 8px 10px;
}

.inline-admin-form button {
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--panel);
  color: var(--text);
  padding: 8px 12px;
  cursor: pointer;
}

.inline-admin-form button:disabled {
  opacity: .55;
  cursor: wait;
}


.key-warning {
  border: 1px solid var(--unknown);
  border-radius: 12px;
  padding: 16px 18px;
  margin: 14px 0;
  background: rgba(213, 168, 79, .08);
}

.key-warning strong,
.key-warning span {
  display: block;
}

.key-warning strong {
  color: #f3d58d;
  margin-bottom: 6px;
}

.key-warning span {
  color: #d8c79e;
  font-size: 12px;
  line-height: 1.5;
}

.advanced-info {
  margin: 14px 0;
}

.advanced-info summary {
  cursor: pointer;
  color: #b9c3d0;
  font-size: 12px;
  font-weight: 700;
}

.advanced-info[open] summary {
  margin-bottom: 10px;
}


.peer-qr-code {
  width: fit-content;
  max-width: 100%;
  margin: 16px auto 0;
  padding: 14px;
  border-radius: 12px;
  background: #fff;
}

.peer-qr-code img,
.peer-qr-code canvas {
  display: block;
  max-width: 100%;
  height: auto;
}


.provisioning-section {
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px solid var(--border);
}

.provisioning-section .placeholder-card + .placeholder-card {
  margin-top: 14px;
}

.subsection-heading {
  margin-bottom: 12px;
}

.subsection-heading .eyebrow {
  margin-bottom: 5px;
}

.subsection-heading h3 {
  margin: 0;
  font-size: 16px;
}

.debug-section {
  margin-top: 30px;
}

.debug-section .advanced-info {
  margin: 0;
}
```
