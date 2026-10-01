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
        listen_path
):
    packet = {
        "protocol_version": 1,
        "session_id": session_id,
        "k_session": k_sess,
        "client_id": client_id,
        "timeout": timeout,
        "created_at": int(time.time()),
        "listen_path": listen_path,
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
        #read response
        with sock.makefile("rb") as response_file:
            response = response_file.readline()
        #check for empty or non-terminated response
        if not response:
            raise ConnectionError(
                "activation socket closed without response"
            )

        response = json.loads(response.decode('utf-8', 'replace').strip())

        return WGClientActivation(sock, response)
    except Exception as e:
        if sock is not None:
            sock.close()
        raise e