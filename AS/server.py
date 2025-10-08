import os
import socket

UDP_IP = "0.0.0.0"
UDP_PORT = 53533
STORE_FILE = os.path.join(os.path.dirname(__file__), "dns_store.txt")

def parse_kv_lines(data: str):
    out = {}
    for line in data.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip().upper()] = v.strip()
    return out

def read_store():
    records = {}
    if not os.path.exists(STORE_FILE):
        return records
    with open(STORE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 4:
                continue
            name, rtype, value, ttl = parts
            records[(name, rtype)] = (value, ttl)
    return records

def write_store(records):
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        for (name, rtype), (value, ttl) in records.items():
            f.write(f"{name}|{rtype}|{value}|{ttl}\n")

def handle_message(msg: str) -> str:
    d = parse_kv_lines(msg)
    msg_type = d.get("TYPE")
    name = d.get("NAME")
    value = d.get("VALUE")
    ttl = d.get("TTL")

    if msg_type != "A" or not name:
        return ""

    records = read_store()

    if value and ttl:
        records[(name, "A")] = (value, ttl)
        write_store(records)
        return f"TYPE=A\nNAME={name}\nVALUE={value}\nTTL={ttl}\n"

    rec = records.get((name, "A"))
    if not rec:
        return ""
    value, ttl = rec
    return f"TYPE=A\nNAME={name}\nVALUE={value}\nTTL={ttl}\n"

def serve():
    if not os.path.exists(STORE_FILE):
        open(STORE_FILE, "a").close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"[AS] Listening UDP {UDP_IP}:{UDP_PORT}")
    while True:
        data, addr = sock.recvfrom(4096)
        try:
            msg = data.decode("utf-8", errors="ignore")
            resp = handle_message(msg)
            if resp:
                sock.sendto(resp.encode("utf-8"), addr)
        except Exception as e:
            print("[AS] Error:", e)

if __name__ == "__main__":
    serve()
PY

