#!/usr/bin/env python3
"""Hermes Chat Bridge v3 - natychmiastowe odpowiedzi przez lokalnego Hermesa, Vox widzi inbox"""
import socket, subprocess, threading, time, os, json, sys

PORT = 17423
HERMES = "/Users/nerucb1/.local/bin/hermes"
INBOX = "/tmp/nexus-inbox.jsonl"

def handle(conn, addr):
    print(f"[BRIDGE] {addr} connected", flush=True)
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

            # ZAPISZ DO INBOXA (zeby Vox widzial)
            with open(INBOX, "a") as f:
                f.write(json.dumps({"ts": time.time(), "from": str(addr), "prompt": prompt}) + "\n")

            # ODPOWIEDZ NATYCHMIAST przez lokalnego Hermesa
            try:
                r = subprocess.run(
                    [HERMES, "--oneshot", prompt, "--yolo"],
                    capture_output=True, text=True, timeout=120,
                    cwd=os.path.expanduser("~"),
                    env={**os.environ, "HOME": os.path.expanduser("~")}
                )
                lines = [l.strip() for l in (r.stdout + r.stderr).split("\n")
                         if l.strip() and not l.startswith("\U0001f9e0") and not l.startswith("\u2139")]
                response = "\n".join(lines[-10:]) if lines else "(empty)"
            except subprocess.TimeoutExpired:
                response = "TIMEOUT (120s)"
            except Exception as e:
                response = f"ERR: {e}"

            conn.sendall((response + "\n").encode())

    except socket.timeout:
        pass
    except Exception as e:
        print(f"[BRIDGE] Error: {e}", flush=True)
    finally:
        conn.close()
        print(f"[BRIDGE] {addr} disconnected", flush=True)

def start(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(10)
    print(f"[BRIDGE v3] :{port} - oneshot + inbox", flush=True)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start(PORT)
