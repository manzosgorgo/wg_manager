# `src/wg_client/wg_client_activator.py`

## Metadata

- Path: `src/wg_client/wg_client_activator.py`
- Language: `python`
- Lines: 117
- SHA256: `87b1338e899054c5e95b37c709441bde52ecc9b9ad8a4efc305af1015912cf0c`
- Imports:
  - `json`
  - `socket`
  - `time`

## Source

```python
import json
import socket
import time

class WGClientActivation:
    def __init__(self, sock, response):
        self.sock = sock
        self.response = response

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

def activate_client(
        socket_path,
        k_sess,
        timeout,
        client_id,
        session_id,
        listen_path,
        principal,
        state_reconcile=None,
):
    packet = {
        "protocol_version": 1,
        "session_id": session_id,
        "k_session": k_sess,
        "client_id": client_id,
        "timeout": timeout,
        "created_at": int(time.time()),
        "listen_path": listen_path,
        "principal": principal,
    }

    payload = (
            json.dumps(
                packet,
                separators=(",", ":")
            ) + "\n"
    ).encode("utf-8")

    sock = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM
    )
    try:
        # connect to the socket and send the payload
        sock.connect(socket_path)
        sock.sendall(payload)
        response_file = sock.makefile("rb")

        while True:
            response = response_file.readline()

            if not response:
                raise ConnectionError(
                    "activation socket closed without response"
                )

            response = json.loads(
                response.decode("utf-8", "replace").strip()
            )

            if not isinstance(response, dict):
                raise ValueError(
                    "activation response must be a JSON object"
                )

            if response.get("protocol_version") != 1:
                raise ValueError(
                    "unsupported activation response protocol_version"
                )

            if response.get("type") == "STATE_SNAPSHOT":
                if state_reconcile is None:
                    raise ValueError(
                        "activation requires state reconciliation"
                    )

                peers = response.get("peers")
                state_reconcile(peers)

                state_result = {
                    "protocol_version": 1,
                    "type": "STATE_RESULT",
                    "status": "OK",
                }

                sock.sendall(
                    (
                        json.dumps(
                            state_result,
                            separators=(",", ":"),
                        )
                        + "\n"
                    ).encode("utf-8")
                )
                continue

            if response.get("type") != "ACTIVATION_RESULT":
                raise ValueError("invalid activation response type")

            if response.get("status") not in {"OK", "ERROR"}:
                raise ValueError("invalid activation response status")

            return WGClientActivation(sock, response)
    except Exception as e:
        if sock is not None:
            sock.close()
        raise e
```
