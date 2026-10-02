# Project Tree

├── apache
│   ├── install
│   │   └── install-apache.sh
│   └── wg-manager.conf
├── cert.old-20260930-145739
│   ├── auth.crt
│   ├── auth.csr
│   ├── auth.ext
│   ├── auth.key
│   ├── ca.crt
│   ├── ca.key
│   ├── ca.srl
│   ├── client.crt
│   ├── client.csr
│   ├── client.ext
│   ├── client.key
│   ├── server.crt
│   ├── server.csr
│   ├── server.ext
│   └── server.key
├── config
│   ├── wg-auth.conf
│   ├── wg-client-test-auth.conf
│   ├── wg-client-test.conf
│   ├── wg-manager-captest.conf
│   ├── wg-manager-realtest.conf
│   └── wg-manager.conf
├── docs
│   ├── README.md
│   ├── _config.yml
│   ├── comm-callgraph.md
│   ├── protocol-flow.md
│   └── static-analysis.md
├── mock
│   └── mock
├── pkg
│   ├── wg-manager-auth-client
│   │   └── DEBIAN
│   │       └── control
│   ├── wg-manager-controller
│   │   └── DEBIAN
│   │       └── control
│   └── README.md
├── src
│   ├── wg_auth
│   │   ├── __init__.py
│   │   ├── wg_auth.py
│   │   ├── wg_auth_API.py
│   │   ├── wg_auth_API_handler.py
│   │   ├── wg_auth_IPC.py
│   │   ├── wg_auth_account_service.py
│   │   ├── wg_auth_errors.py
│   │   ├── wg_auth_lifecycle.py
│   │   ├── wg_auth_ownership_service.py
│   │   ├── wg_auth_peer_registry.py
│   │   ├── wg_auth_session.py
│   │   └── wg_auth_user_store.py
│   ├── wg_client
│   │   ├── __init__.py
│   │   ├── wg_client.py
│   │   ├── wg_client_API.py
│   │   ├── wg_client_API_handler.py
│   │   ├── wg_client_IPC.py
│   │   ├── wg_client_activator.py
│   │   ├── wg_client_config.py
│   │   ├── wg_client_errors.js
│   │   ├── wg_client_errors.py
│   │   ├── wg_client_lifecycle.py
│   │   ├── wg_controller_client.py
│   │   ├── wg_peer_service.py
│   │   └── wg_secure_session.py
│   ├── wg_frontend
│   │   ├── vendor
│   │   │   └── LICENSE.libopaque
│   │   ├── www
│   │   │   └── vpn
│   │   │       ├── vendor
│   │   │       │   ├── qrcode.LICENSE
│   │   │       │   └── qrcode.min.js
│   │   │       ├── app.js
│   │   │       ├── index.html
│   │   │       └── style.css
│   │   ├── __init__.py
│   │   ├── check_vectors.mjs
│   │   ├── package.json
│   │   ├── test_wg_secure_session_vectors.json
│   │   ├── wg_auth_session.js
│   │   ├── wg_client_api.js
│   │   ├── wg_client_errors.js
│   │   ├── wg_opaque_client.js
│   │   ├── wg_secure_session.js
│   │   └── wg_secure_session_vector_input.json
│   ├── wg_manager
│   │   └── wg_manager.py
│   └── __init__.py
├── systemd
│   ├── install
│   │   ├── install-auth-service.sh
│   │   ├── install-client-service.sh
│   │   └── install-server-service.sh
│   ├── production
│   │   ├── wg-auth.service
│   │   ├── wg-client.socket
│   │   ├── wg-client@.service
│   │   ├── wg-manager.socket
│   │   └── wg-manager@.service
│   ├── wg-auth.service
│   ├── wg-client-test.socket
│   ├── wg-client-test@.service
│   ├── wg-client-test@.service.bak
│   ├── wg-controller-test.socket
│   ├── wg-controller-test@.service
│   └── wg_client.conf
├── tests
│   ├── auth
│   │   ├── js
│   │   │   ├── client_cli.js
│   │   │   ├── opaque_client.js
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   ├── test_auth.conf
│   │   │   └── wg_auth_client.js
│   │   ├── __init__.py
│   │   ├── test_account_service.py
│   │   ├── test_auth_api_state.py
│   │   ├── test_ownership_service.py
│   │   ├── test_peer_registry.py
│   │   └── test_user_store.py
│   ├── client
│   │   ├── __init__.py
│   │   ├── test_admin_ipc.py
│   │   ├── test_peer_service.py
│   │   ├── test_secure_session.py
│   │   ├── test_secure_session_concurrency.py
│   │   ├── test_secure_session_policy.py
│   │   ├── test_secure_session_threadsefety.py
│   │   ├── test_wg_client_activator.py
│   │   └── test_wg_client_integration.py
│   ├── e2e
│   │   ├── test_js_full_flow.mjs
│   │   └── test_js_user_lifecycle.mjs
│   ├── frontend
│   │   ├── __init__.py
│   │   ├── test_cross_language_vector.py
│   │   ├── test_secure_session_concurrency.test.mjs
│   │   └── wg_secure_session_gen_vectors.py
│   ├── __init__.py
│   └── test_mock.py
├── .gitignore
├── README.md
├── TODO.md
├── compile_commands.json
└── pyproject.toml
