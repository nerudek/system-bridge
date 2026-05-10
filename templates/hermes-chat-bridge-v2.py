#!/usr/bin/env python3
"""Hermes Chat Bridge v2 — bidirectional chat via Vox inbox (no oneshot spawn)"""
import socket, json, threading, time, os, sys, uuid

PORT = 17423
INBOX = "/tmp/nexus-inbox.jsonl"
OUTBOX_DIR = "/tmp/nexus-outbox"
os.makedirs(OUTBOX_DIR, exist_ok=True)

def handle(conn, addr):
    print(f"[CHAT] {addr} connected", flush=True)
    try:
        conn.settimeout(300)
        while True:
            data = conn.recv(8192)
            if not data:
                break
            prompt = data.decode().strip()
            if prompt.lower() in ("exit", "quit", "bye"):
                conn.sendall(b"BYE\n")
                break

            msg_id = str(uuid.uuid4())[:8]
            msg = {"id": msg_id, "ts": time.time(), "from": "nexus", "addr": str(addr), "prompt": prompt}

            with open(INBOX, "a") as f:
                f.write(json.dumps(msg) + "\n")

            outbox_file = os.path.join(OUTBOX_DIR, f"{msg_id}.json")
            waited = 0
            while waited < 180:
                if os.path.exists(outbox_file):
                    time.sleep(0.2)
                    with open(outbox_file) as f:
                        resp = json.load(f)
                    os.remove(outbox_file)
                    response_text = resp.get("response", "(empty)")
                    conn.sendall((response_text + "\n").encode())
                    break
                time.sleep(0.5)
                waited += 0.5
            else:
                conn.sendall(b"TIMEOUT: Vox nie odpowiedzial w 180s\n")

    except socket.timeout:
        conn.sendall(b"TIMEOUT: polaczenie bezczynne 300s\n")
    except Exception as e:
        conn.sendall(f"ERR: {e}\n".encode())
    finally:
        conn.close()
        print(f"[CHAT] {addr} disconnected", flush=True)

def start(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    print(f"[CHAT v2] port {port} — forwarding to Vox inbox", flush=True)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start(PORT)
