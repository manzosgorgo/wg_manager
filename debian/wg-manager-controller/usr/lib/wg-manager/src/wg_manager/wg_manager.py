#!/usr/bin/env python3
"""
Privileged socket-activated WireGuard controller.

Each systemd Accept=yes instance receives one connected TCP socket on file
descriptor 3, upgrades it to TLS 1.3 with mandatory client certificates,
parses one bounded HTTP/1.1 request, applies policy to the configured WireGuard
interface through the wg executable, replies with JSON and exits.
"""

import base64, configparser, ipaddress, json, os, socket, ssl, subprocess, sys
from http import HTTPStatus
from urllib.parse import unquote

CONFIG = os.environ.get("WG_CONFIG")
WG_PROGRAM = os.environ.get("WG_PROGRAM", "/usr/bin/wg")

if not CONFIG:
    raise RuntimeError("WG_CONFIG is not set")


def log(msg):
    """
    Write one controller diagnostic line to stderr.
    """
    print(f"[wg_manager] {msg}", file=sys.stderr, flush=True)


class E(Exception):
    """
    Internal request error carrying the HTTP status and public error message.
    """
    def __init__(self, code, msg):
        """
        Create an internal controller error with HTTP status and message.
        """
        self.code, self.msg = code, msg


def cfg():
    """
    Load WG_CONFIG and return normalized interface, TLS and VPN policy values.
    """
    c = configparser.ConfigParser()
    if not c.read(CONFIG):
        raise RuntimeError(f"cannot read {CONFIG}")
    return {
        "if": c["manager"]["interface"].strip(),
        "server_cert": c["tls"]["server_cert"].strip(),
        "server_key": c["tls"]["server_key"].strip(),
        "client_ca": c["tls"]["client_ca"].strip(),
        "net": ipaddress.ip_network(c["policy"]["vpn_network"].strip(), strict=False),
        "server_address": c["policy"].get("server_address", "").strip() or None,
    }


def reply(s, code, obj):
    """
    Send one JSON HTTP/1.1 response and close-oriented headers.
    """
    b = json.dumps(obj, separators=(",", ":")).encode()
    h = (
        f"HTTP/1.1 {code} {HTTPStatus(code).phrase}\r\nContent-Type: application/json\r\nContent-Length: {len(b)}\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n"
    ).encode()
    s.sendall(h + b)


def request(s):
    """
    Read and validate one bounded HTTP/1.1 request from the connected socket.
    """
    s.settimeout(10)
    d = b""
    while b"\r\n\r\n" not in d:
        x = s.recv(4096)
        if not x:
            raise E(400, "incomplete request")
        d += x
        if len(d) > 16384:
            raise E(413, "headers too large")
    head, body = d.split(b"\r\n\r\n", 1)
    lines = head.decode("iso-8859-1").split("\r\n")
    p = lines[0].split()
    if len(p) != 3 or p[2] != "HTTP/1.1":
        raise E(400, "HTTP/1.1 required")
    H = {}
    for l in lines[1:]:
        if ":" not in l:
            raise E(400, "malformed header")
        k, v = l.split(":", 1)
        H[k.lower().strip()] = v.strip()
    try:
        n = int(H.get("content-length", "0"))
    except ValueError:
        raise E(400, "invalid Content-Length")
    if n > 65536:
        raise E(413, "body too large")
    while len(body) < n:
        x = s.recv(min(4096, n - len(body)))
        if not x:
            raise E(400, "incomplete body")
        body += x
    return p[0], p[1], body[:n]


def wg(args):
    """
    Execute the configured wg program with a five-second timeout and return stdout.
    """
    #    log(f"wg {' '.join(args)}")
    p = subprocess.run(
        [WG_PROGRAM, *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=5,
    )
    if p.returncode:
        raise E(500, "WireGuard operation failed")
    return p.stdout


def key(k):
    """
    Validate a standard-base64 WireGuard public key and return it unchanged.
    """
    try:
        b = base64.b64decode(k, validate=True)
    except Exception:
        raise E(400, "invalid public_key")
    if len(b) != 32:
        raise E(400, "invalid public_key")
    return k


def peers(interface):
    """
    Return normalized peer state parsed from wg show INTERFACE dump.
    """
    out = wg(["show", interface, "dump"])
    r = []
    for l in out.splitlines()[1:]:
        f = l.split("\t")
        if len(f) >= 8:
            r.append(
                {
                    "public_key": f[0],
                    "allowed_ips": f[3].split(",") if f[3] else [],
                    "endpoint": f[2],
                    "latest_handshake": int(f[4]) if f[4].isdigit() else 0,
                    "rx_bytes": int(f[5]) if f[5].isdigit() else 0,
                    "tx_bytes": int(f[6]) if f[6].isdigit() else 0,
                }
            )
    return r


def provisioning(c):
    """
    Return public key, listen port, VPN policy and currently used host addresses.
    """
    out = wg(["show", c["if"], "dump"])
    lines = out.splitlines()

    if not lines:
        raise E(500, "WireGuard interface state unavailable")

    interface = lines[0].split("\t")
    if len(interface) < 4:
        raise E(500, "invalid WireGuard interface state")

    used_ips = []
    for peer in peers(c["if"]):
        for allowed_ip in peer.get("allowed_ips", []):
            try:
                candidate = ipaddress.ip_interface(allowed_ip)
            except ValueError:
                continue

            if (
                candidate.version == c["net"].version
                and candidate.network.prefixlen == candidate.max_prefixlen
                and candidate.ip in c["net"]
            ):
                used_ips.append(str(candidate))

    return {
        "ok": True,
        "interface": c["if"],
        "server_public_key": interface[1],
        "listen_port": int(interface[2]) if interface[2].isdigit() else 0,
        "vpn_network": str(c["net"]),
        "server_address": c["server_address"],
        "used_ips": sorted(set(used_ips)),
    }


def add(c, o):
    """
    Validate policy/uniqueness and add one WireGuard peer.
    """
    if not isinstance(o, dict):
        raise E(400, "JSON object required")
    pk = key(o.get("public_key", ""))
    try:
        ip = ipaddress.ip_interface(o.get("allowed_ip", ""))
    except ValueError:
        raise E(400, "invalid allowed_ip")
    if ip.network.prefixlen != 32 or ip.ip not in c["net"]:
        raise E(400, "allowed_ip outside VPN network")
    ip = str(ip)
    for p in peers(c["if"]):
        if p["public_key"] == pk:
            raise E(409, "peer already exists")
        if str(ip) in p["allowed_ips"]:
            raise E(409, "allowed_ip already in use")
    wg(["set", c["if"], "peer", pk, "allowed-ips", ip])
    return {"ok": True, "operation": "add_peer", "public_key": pk, "allowed_ip": ip}


def remove(c, pk):
    """
    Validate existence and remove one WireGuard peer.
    """
    pk = key(pk)
    if not any(p["public_key"] == pk for p in peers(c["if"])):
        raise E(404, "peer not found")
    wg(["set", c["if"], "peer", pk, "remove"])
    return {"ok": True, "operation": "remove_peer", "public_key": pk}


def dispatch(c, m, t, b):
    """
    Route the controller HTTP method/target to status, provisioning or peer mutation.
    """
    if m == "GET" and t == "/v1/status":
        return 200, {"ok": True, "interface": c["if"], "peers": peers(c["if"])}
    if m == "GET" and t == "/v1/provisioning":
        return 200, provisioning(c)
    if m == "POST" and t == "/v1/peers":
        try:
            o = json.loads(b.decode())
        except Exception:
            raise E(400, "invalid JSON")
        return 201, add(c, o)
    pre = "/v1/peers/"
    if m == "DELETE" and t.startswith(pre):
        return 200, remove(c, unquote(t[len(pre) :]))
    raise E(404, "endpoint not found")


def systemd_socket():
    """
    Adopt exactly one socket passed by systemd socket activation on file descriptor 3.
    """
    pid = os.environ.get("LISTEN_PID")
    nfds = os.environ.get("LISTEN_FDS")

    if pid != str(os.getpid()):
        raise RuntimeError("invalid LISTEN_PID")

    if nfds != "1":
        raise RuntimeError(f"expected 1 socket, got {nfds}")

    return socket.socket(fileno=3)


def tls(c):
    """
    Wrap the inherited socket in TLS 1.3 and require a client certificate from the configured CA.
    """
    raw = systemd_socket()
    raw.settimeout(10)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_cert_chain(c["server_cert"], c["server_key"])
    ctx.load_verify_locations(cafile=c["client_ca"])

    return ctx.wrap_socket(raw, server_side=True)


def main():
    """
    Process one socket-activated controller request and return a process exit status.
    """
    c = cfg()
    s = None
    try:
        s = tls(c)

        m, t, b = request(s)
        #        log(f"request {m} {t}")

        code, obj = dispatch(c, m, t, b)
        reply(s, code, obj)
        return 0
    except E as e:
        if s:
            try:
                reply(s, e.code, {"ok": False, "error": e.msg})
            except OSError:
                pass
        return 0
    except ssl.SSLError as e:
        print(f"TLS error: {e!r}", file=sys.stderr, flush=True)
        return 1
    except Exception as e:
        print(f"Unhandled exception: {e!r}", file=sys.stderr, flush=True)
        if s:
            try:
                reply(s, 500, {"ok": False, "error": "internal error"})
            except OSError:
                pass
        return 1
    finally:
        if s:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()


if __name__ == "__main__":
    sys.exit(main())
