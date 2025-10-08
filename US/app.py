from flask import Flask, request, jsonify, make_response
import socket
import requests

app = Flask(__name__)

def dns_query(as_ip: str, as_port: int, hostname: str) -> str | None:
    """Returns IP string or None if not found/error."""
    msg = f"TYPE=A\nNAME={hostname}\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    try:
        sock.sendto(msg.encode("utf-8"), (as_ip, as_port))
        data, _ = sock.recvfrom(4096)
        resp = data.decode("utf-8", errors="ignore")
        # Expect VALUE line
        ip = None
        for line in resp.splitlines():
            if line.strip().upper().startswith("VALUE="):
                ip = line.split("=", 1)[1].strip()
                break
        return ip
    except Exception:
        return None
    finally:
        sock.close()

@app.get("/fibonacci")
def fibonacci_proxy():
    # Required query params
    hostname = request.args.get("hostname", type=str)
    fs_port = request.args.get("fs_port", type=str)
    number = request.args.get("number", type=str)
    as_ip = request.args.get("as_ip", type=str)
    as_port = request.args.get("as_port", type=str)

    if not all([hostname, fs_port, number, as_ip, as_port]):
        return make_response("Missing required parameters", 400)

    try:
        fs_port_i = int(fs_port)
        as_port_i = int(as_port)
    except Exception:
        return make_response("fs_port and as_port must be integers", 400)

    # DNS query to get IP for hostname
    ip = dns_query(as_ip, as_port_i, hostname)
    if not ip:
        return make_response("DNS lookup failed or record not found", 502)

    # Call FS
    try:
        r = requests.get(f"http://{ip}:{fs_port_i}/fibonacci", params={"number": number}, timeout=2.0)
    except Exception as e:
        return make_response(f"FS request failed: {e}", 502)

    # Pass through FS response appropriately
    if r.status_code == 200:
        # Return the Fibonacci number (just forward JSON)
        return make_response(r.text, 200)
    elif r.status_code == 400:
        return make_response("Bad number format", 400)
    else:
        return make_response(f"FS error {r.status_code}", 502)

if __name__ == "__main__":
    # Port 8080 per spec
    app.run(host="0.0.0.0", port=8080)
