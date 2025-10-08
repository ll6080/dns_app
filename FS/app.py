from flask import Flask, request, jsonify, make_response
import socket

app = Flask(__name__)

def send_udp(as_ip: str, as_port: int, message: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(message.encode("utf-8"), (as_ip, as_port))
        # Optionally read response (not required to confirm registration)
        sock.settimeout(1.0)
        try:
            _data, _addr = sock.recvfrom(4096)
        except socket.timeout:
            pass
    finally:
        sock.close()

def fib(n: int) -> int:
    if n < 0:
        raise ValueError("Negative not allowed")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a+b
    return a

@app.put("/register")
def register():
    try:
        body = request.get_json(force=True, silent=False)
    except Exception:
        return make_response("Invalid JSON", 400)

    required = ["hostname", "ip", "as_ip", "as_port"]
    if any(k not in body or body[k] in (None, "") for k in required):
        return make_response("Missing required fields", 400)

    hostname = body["hostname"]
    ip = body["ip"]
    as_ip = body["as_ip"]
    try:
        as_port = int(body["as_port"])
    except Exception:
        return make_response("as_port must be integer", 400)

    dns_msg = f"TYPE=A\nNAME={hostname}\nVALUE={ip}\nTTL=10\n"
    try:
        send_udp(as_ip, as_port, dns_msg)
    except Exception as e:
        return make_response(f"Registration UDP send failed: {e}", 500)

    return make_response("", 201)

@app.get("/fibonacci")
def fibonacci():
    x = request.args.get("number", type=str)
    if x is None:
        return make_response("Missing number", 400)
    try:
        n = int(x)
    except Exception:
        return make_response("number must be integer", 400)

    try:
        value = fib(n)
    except ValueError as e:
        return make_response(str(e), 400)

    return jsonify({"result": value}), 200

if __name__ == "__main__":
    # Port 9090 per spec
    app.run(host="0.0.0.0", port=9090)
