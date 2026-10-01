# `tests/test_http_handler.py`

## Metadata

- Path: `tests/test_http_handler.py`
- Language: `python`
- Lines: 171
- SHA256: `e43b17faefda012196b959e9ccf47dd8651f7061181e9fb5e2a2ceb48f283b5d`
- Imports:
  - `logging`
  - `socket`
  - `ssl`
  - `tests.client.test_wg_handler`

## Source

```python
#!/usr/bin/env python3

import logging
import socket
import ssl

from tests.client.test_wg_handler import WGClientAPIHandler


HOST = "127.0.0.1"
PORT = 9445

CERT_FILE = "//cert/server.crt"
KEY_FILE = "//cert/server.key"
CA_FILE = "//cert/ca.crt"


log = logging.getLogger("wg_manager.http-test")


class DummyServer:
    """
    Minimalissimo oggetto server richiesto da BaseHTTPRequestHandler.

    Non è un HTTPServer.
    Serve solamente a fornire al handler le informazioni
    che normalmente riceverebbe dal vero HTTPServer.
    """

    def __init__(self, host, port):
        self.server_name = host
        self.server_port = port


def create_tls_context():
    log.info("Creating TLS server context")

    context = ssl.SSLContext(
        ssl.PROTOCOL_TLS_SERVER
    )

    context.minimum_version = ssl.TLSVersion.TLSv1_3

    context.load_cert_chain(
        certfile=CERT_FILE,
        keyfile=KEY_FILE
    )

    # mTLS
    context.load_verify_locations(
        cafile=CA_FILE
    )

    context.verify_mode = ssl.CERT_REQUIRED

    log.info("TLS context ready")

    return context


# noinspection broad-exception
def handle_connection(connection, address, context):
    log.info(
        "Accepted TCP connection from %s:%d",
        address[0],
        address[1]
    )

    try:
        log.info("Starting TLS handshake")

        tls_connection = context.wrap_socket(
            connection,
            server_side=True
        )

        log.info(
            "TLS established with %s",
            address[0]
        )

        dummy_server = DummyServer(
            HOST,
            PORT
        )

        log.info("Creating WGClientAPIHandler")

        WGClientAPIHandler(
            tls_connection,
            address,
            dummy_server
        )

        log.info("WGClientAPIHandler finished")

    except ssl.SSLError as exc:
        log.error(
            "TLS error: %s",
            exc
        )

    except Exception:
        log.exception(
            "Exception while handling HTTP connection"
        )

    finally:
        try:
            # noinspection unbound-local-variable
            tls_connection.close()
        except UnboundLocalError:
            connection.close()


def main():

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s"
    )

    log.info("=== HTTP handler test starting ===")

    context = create_tls_context()

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind(
        (HOST, PORT)
    )

    server_socket.listen(1)

    log.info(
        "Listening on %s:%d",
        HOST,
        PORT
    )

    try:
        while True:

            connection, address = server_socket.accept()

            handle_connection(
                connection,
                address,
                context
            )

    except KeyboardInterrupt:
        log.info("Stopping HTTP handler test")

    finally:
        server_socket.close()

    log.info("=== HTTP handler test finished ===")


if __name__ == "__main__":
    main()
```
