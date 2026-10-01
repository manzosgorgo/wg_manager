# Project Tree

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
│   ├── gestione_permessi_uid_gid.md
│   ├── protocol-flow.md
│   ├── static-analysis.md
│   ├── wg-client-api.md
│   └── wg-secure-session-docs.md
├── mock
│   └── mock
├── src
│   ├── wg_auth
│   │   ├── __init__.py
│   │   ├── wg_auth.py
│   │   ├── wg_auth_API.py
│   │   ├── wg_auth_API_handler.py
│   │   ├── wg_auth_IPC.py
│   │   ├── wg_auth_errors.py
│   │   ├── wg_auth_lifecycle.py
│   │   └── wg_auth_session.py
│   ├── wg_client
│   │   ├── __init__.py
│   │   ├── wg_client.py
│   │   ├── wg_client_API.py
│   │   ├── wg_client_API_handler.py
│   │   ├── wg_client_IPC.py
│   │   ├── wg_client_activator.py
│   │   ├── wg_client_config.py
│   │   ├── wg_client_errors.py
│   │   ├── wg_client_lifecycle.py
│   │   ├── wg_controller_client.py
│   │   └── wg_secure_session.py
│   ├── wg_frontend
│   │   ├── __init__.py
│   │   ├── check_vectors.mjs
│   │   ├── package.json
│   │   ├── test_wg_secure_session_vectors.json
│   │   ├── wg_auth_session.js
│   │   ├── wg_client_errors.js
│   │   ├── wg_secure_session.js
│   │   └── wg_secure_session_vector_input.json
│   ├── wg_manager
│   │   └── wg_manager.py
│   └── __init__.py
├── systemd
│   ├── install
│   │   ├── install-client-service.sh
│   │   └── install-server-service.sh
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
│   │   ├── test_auth_races.py
│   │   ├── test_wg_auth.js
│   │   └── test_wg_auth.py
│   ├── client
│   │   ├── __init__.py
│   │   ├── test_auth_client.py
│   │   ├── test_client.py
│   │   ├── test_client_API.py
│   │   ├── test_secure_session.py
│   │   ├── test_wg_client_activator.py
│   │   └── test_wg_client_integration.py
│   ├── frontend
│   │   ├── __init__.py
│   │   ├── test_cross_language_vector.py
│   │   └── wg_secure_session_gen_vectors.py
│   ├── __init__.py
│   └── test_http_handler.py
├── README.md
├── TODO.md
├── compile_commands.json
└── pyproject.toml
