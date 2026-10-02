# Modules / Directories

This file is generated automatically.

| Directory | Files |
|---|---:|
| `/` | 5 |
| `apache` | 1 |
| `apache/install` | 1 |
| `apache/production` | 1 |
| `cert.old-20260930-145739` | 15 |
| `config` | 6 |
| `config/production` | 3 |
| `debian` | 25 |
| `debian/.debhelper/generated/wg-manager-auth-client` | 5 |
| `debian/.debhelper/generated/wg-manager-controller` | 5 |
| `debian/sysusers` | 2 |
| `debian/wg-manager-auth-client/DEBIAN` | 7 |
| `debian/wg-manager-auth-client/etc/apache2/conf-available` | 1 |
| `debian/wg-manager-auth-client/etc/wg-manager` | 2 |
| `debian/wg-manager-auth-client/usr/lib/systemd/system` | 3 |
| `debian/wg-manager-auth-client/usr/lib/sysusers.d` | 1 |
| `debian/wg-manager-auth-client/usr/lib/tmpfiles.d` | 1 |
| `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth` | 12 |
| `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client` | 12 |
| `debian/wg-manager-auth-client/usr/sbin` | 2 |
| `debian/wg-manager-auth-client/usr/share/doc/wg-manager-auth-client` | 5 |
| `debian/wg-manager-auth-client/usr/share/wg-manager/frontend` | 3 |
| `debian/wg-manager-auth-client/usr/share/wg-manager/frontend/vendor` | 2 |
| `debian/wg-manager-auth-client/usr/share/wg-manager/js` | 5 |
| `debian/wg-manager-auth-client/usr/share/wg-manager/js/vendor` | 1 |
| `debian/wg-manager-controller/DEBIAN` | 7 |
| `debian/wg-manager-controller/etc/wg-manager` | 1 |
| `debian/wg-manager-controller/usr/lib/systemd/system` | 2 |
| `debian/wg-manager-controller/usr/lib/sysusers.d` | 1 |
| `debian/wg-manager-controller/usr/lib/wg-manager/src/wg_manager` | 1 |
| `debian/wg-manager-controller/usr/sbin` | 1 |
| `debian/wg-manager-controller/usr/share/doc/wg-manager-controller` | 4 |
| `docs` | 7 |
| `mock` | 1 |
| `pkg` | 1 |
| `src` | 1 |
| `src/wg_auth` | 12 |
| `src/wg_client` | 13 |
| `src/wg_frontend` | 10 |
| `src/wg_frontend/vendor` | 1 |
| `src/wg_frontend/www/vpn` | 3 |
| `src/wg_frontend/www/vpn/vendor` | 2 |
| `src/wg_manager` | 1 |
| `systemd` | 6 |
| `systemd/install` | 3 |
| `systemd/production` | 5 |
| `tests` | 2 |
| `tests/auth` | 6 |
| `tests/auth/js` | 6 |
| `tests/client` | 9 |
| `tests/e2e` | 2 |
| `tests/frontend` | 4 |
| `vendor` | 1 |

## Contents

### `/`

- `.gitignore`
- `README.md`
- `TODO.md`
- `compile_commands.json`
- `pyproject.toml`

### `apache`

- `wg-manager.conf`

### `apache/install`

- `install-apache.sh`

### `apache/production`

- `wg-manager.conf`

### `cert.old-20260930-145739`

- `auth.crt`
- `auth.csr`
- `auth.ext`
- `auth.key`
- `ca.crt`
- `ca.key`
- `ca.srl`
- `client.crt`
- `client.csr`
- `client.ext`
- `client.key`
- `server.crt`
- `server.csr`
- `server.ext`
- `server.key`

### `config`

- `wg-auth.conf`
- `wg-client-test-auth.conf`
- `wg-client-test.conf`
- `wg-manager-captest.conf`
- `wg-manager-realtest.conf`
- `wg-manager.conf`

### `config/production`

- `wg-auth.conf`
- `wg-client.conf`
- `wg-manager.conf`

### `debian`

- `certificates.README`
- `changelog`
- `control`
- `debhelper-build-stamp`
- `files`
- `rules`
- `wg-manager-auth-client.debhelper.log`
- `wg-manager-auth-client.dirs`
- `wg-manager-auth-client.install`
- `wg-manager-auth-client.postinst`
- `wg-manager-auth-client.postinst.debhelper`
- `wg-manager-auth-client.postrm`
- `wg-manager-auth-client.postrm.debhelper`
- `wg-manager-auth-client.prerm`
- `wg-manager-auth-client.substvars`
- `wg-manager-auth-client.tmpfiles`
- `wg-manager-controller.debhelper.log`
- `wg-manager-controller.dirs`
- `wg-manager-controller.install`
- `wg-manager-controller.postinst`
- `wg-manager-controller.postrm`
- `wg-manager-controller.postrm.debhelper`
- `wg-manager-controller.prerm`
- `wg-manager-controller.substvars`
- `wg-manager-users`

### `debian/.debhelper/generated/wg-manager-auth-client`

- `dh_installchangelogs.dch.trimmed`
- `installed-by-dh_install`
- `installed-by-dh_installdocs`
- `postinst.service`
- `preinst.service`

### `debian/.debhelper/generated/wg-manager-controller`

- `dh_installchangelogs.dch.trimmed`
- `installed-by-dh_install`
- `installed-by-dh_installdocs`
- `postinst.service`
- `preinst.service`

### `debian/sysusers`

- `wg-manager-auth-client.conf`
- `wg-manager-controller.conf`

### `debian/wg-manager-auth-client/DEBIAN`

- `conffiles`
- `control`
- `md5sums`
- `postinst`
- `postrm`
- `preinst`
- `prerm`

### `debian/wg-manager-auth-client/etc/apache2/conf-available`

- `wg-manager.conf`

### `debian/wg-manager-auth-client/etc/wg-manager`

- `wg-auth.conf`
- `wg-client.conf`

### `debian/wg-manager-auth-client/usr/lib/systemd/system`

- `wg-auth.service`
- `wg-client.socket`
- `wg-client@.service`

### `debian/wg-manager-auth-client/usr/lib/sysusers.d`

- `wg-manager-auth-client.conf`

### `debian/wg-manager-auth-client/usr/lib/tmpfiles.d`

- `wg-manager-auth-client.conf`

### `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_auth`

- `__init__.py`
- `wg_auth.py`
- `wg_auth_API.py`
- `wg_auth_API_handler.py`
- `wg_auth_IPC.py`
- `wg_auth_account_service.py`
- `wg_auth_errors.py`
- `wg_auth_lifecycle.py`
- `wg_auth_ownership_service.py`
- `wg_auth_peer_registry.py`
- `wg_auth_session.py`
- `wg_auth_user_store.py`

### `debian/wg-manager-auth-client/usr/lib/wg-manager/src/wg_client`

- `__init__.py`
- `wg_client.py`
- `wg_client_API.py`
- `wg_client_API_handler.py`
- `wg_client_IPC.py`
- `wg_client_activator.py`
- `wg_client_config.py`
- `wg_client_errors.py`
- `wg_client_lifecycle.py`
- `wg_controller_client.py`
- `wg_peer_service.py`
- `wg_secure_session.py`

### `debian/wg-manager-auth-client/usr/sbin`

- `wg-manager-check-auth-client`
- `wg-manager-users`

### `debian/wg-manager-auth-client/usr/share/doc/wg-manager-auth-client`

- `LICENSE.libopaque.gz`
- `certificates.README`
- `changelog.Debian.gz`
- `configuration.md.gz`
- `deployment.md.gz`

### `debian/wg-manager-auth-client/usr/share/wg-manager/frontend`

- `app.js`
- `index.html`
- `style.css`

### `debian/wg-manager-auth-client/usr/share/wg-manager/frontend/vendor`

- `qrcode.LICENSE`
- `qrcode.min.js`

### `debian/wg-manager-auth-client/usr/share/wg-manager/js`

- `wg_auth_session.js`
- `wg_client_api.js`
- `wg_client_errors.js`
- `wg_opaque_client.js`
- `wg_secure_session.js`

### `debian/wg-manager-auth-client/usr/share/wg-manager/js/vendor`

- `libopaque.js`

### `debian/wg-manager-controller/DEBIAN`

- `conffiles`
- `control`
- `md5sums`
- `postinst`
- `postrm`
- `preinst`
- `prerm`

### `debian/wg-manager-controller/etc/wg-manager`

- `wg-manager.conf`

### `debian/wg-manager-controller/usr/lib/systemd/system`

- `wg-manager.socket`
- `wg-manager@.service`

### `debian/wg-manager-controller/usr/lib/sysusers.d`

- `wg-manager-controller.conf`

### `debian/wg-manager-controller/usr/lib/wg-manager/src/wg_manager`

- `wg_manager.py`

### `debian/wg-manager-controller/usr/sbin`

- `wg-manager-check-controller`

### `debian/wg-manager-controller/usr/share/doc/wg-manager-controller`

- `certificates.README`
- `changelog.Debian.gz`
- `configuration.md.gz`
- `deployment.md.gz`

### `docs`

- `README.md`
- `_config.yml`
- `comm-callgraph.md`
- `configuration.md`
- `deployment.md`
- `protocol-flow.md`
- `static-analysis.md`

### `mock`

- `mock`

### `pkg`

- `README.md`

### `src`

- `__init__.py`

### `src/wg_auth`

- `__init__.py`
- `wg_auth.py`
- `wg_auth_API.py`
- `wg_auth_API_handler.py`
- `wg_auth_IPC.py`
- `wg_auth_account_service.py`
- `wg_auth_errors.py`
- `wg_auth_lifecycle.py`
- `wg_auth_ownership_service.py`
- `wg_auth_peer_registry.py`
- `wg_auth_session.py`
- `wg_auth_user_store.py`

### `src/wg_client`

- `__init__.py`
- `wg_client.py`
- `wg_client_API.py`
- `wg_client_API_handler.py`
- `wg_client_IPC.py`
- `wg_client_activator.py`
- `wg_client_config.py`
- `wg_client_errors.js`
- `wg_client_errors.py`
- `wg_client_lifecycle.py`
- `wg_controller_client.py`
- `wg_peer_service.py`
- `wg_secure_session.py`

### `src/wg_frontend`

- `__init__.py`
- `check_vectors.mjs`
- `package.json`
- `test_wg_secure_session_vectors.json`
- `wg_auth_session.js`
- `wg_client_api.js`
- `wg_client_errors.js`
- `wg_opaque_client.js`
- `wg_secure_session.js`
- `wg_secure_session_vector_input.json`

### `src/wg_frontend/vendor`

- `LICENSE.libopaque`

### `src/wg_frontend/www/vpn`

- `app.js`
- `index.html`
- `style.css`

### `src/wg_frontend/www/vpn/vendor`

- `qrcode.LICENSE`
- `qrcode.min.js`

### `src/wg_manager`

- `wg_manager.py`

### `systemd`

- `wg-auth.service`
- `wg-client-test.socket`
- `wg-client-test@.service`
- `wg-controller-test.socket`
- `wg-controller-test@.service`
- `wg_client.conf`

### `systemd/install`

- `install-auth-service.sh`
- `install-client-service.sh`
- `install-server-service.sh`

### `systemd/production`

- `wg-auth.service`
- `wg-client.socket`
- `wg-client@.service`
- `wg-manager.socket`
- `wg-manager@.service`

### `tests`

- `__init__.py`
- `test_mock.py`

### `tests/auth`

- `__init__.py`
- `test_account_service.py`
- `test_auth_api_state.py`
- `test_ownership_service.py`
- `test_peer_registry.py`
- `test_user_store.py`

### `tests/auth/js`

- `client_cli.js`
- `opaque_client.js`
- `package-lock.json`
- `package.json`
- `test_auth.conf`
- `wg_auth_client.js`

### `tests/client`

- `__init__.py`
- `test_admin_ipc.py`
- `test_peer_service.py`
- `test_secure_session.py`
- `test_secure_session_concurrency.py`
- `test_secure_session_policy.py`
- `test_secure_session_threadsefety.py`
- `test_wg_client_activator.py`
- `test_wg_client_integration.py`

### `tests/e2e`

- `test_js_full_flow.mjs`
- `test_js_user_lifecycle.mjs`

### `tests/frontend`

- `__init__.py`
- `test_cross_language_vector.py`
- `test_secure_session_concurrency.test.mjs`
- `wg_secure_session_gen_vectors.py`

### `vendor`

- `libopaque.js`
