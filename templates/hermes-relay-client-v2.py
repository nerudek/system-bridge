#!/usr/bin/env python3
"""Relay Client v2 - autonomiczny, odpowiada przez oneshot, zapisuje do inbox"""
import socket, subprocess, threading, time, os, sys, json

RELAY_HOST = "127.0.0.1"
RELAY_PORT = 17426
NAME = "MAC-MINI-HERMES"
HERMES = "/Users/nerucb1/.local/bin/hermes"
INBOX = "/tmp/nexus-inbox.jsonl"

def connect():
    while True:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((RELAY_HOST, RELAY_PORT))
            conn.sendall((NAME + "\n").encode())
            print(f"[RELAY] Connected as {NAME}", flush=True)
            return conn
        except Exception as e:
            print(f"[RELAY] Connect failed: {e}, retry in 5s", flush=True)
            time.sleep(5)

def respond(conn, prompt):
    # Zapisz do inbox Voxa
    with open(INBOX, "a") as f:
        f.write(json.dumps({"ts": time.time(), "from": "relay", "prompt": prompt}) + "\n")

    # Odpowiedz natychmiast przez lokalnego Hermesa
    try:
        r = subprocess.run(
            [HERMES, "--oneshot", prompt, "--yolo"],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.expanduser("~"),
            env={**os.environ, "HOME": os.path.expanduser("~")}
        )
        lines = [l.strip() for l in (r.stdout + r.stderr).split("\n")
                 if l.strip() and not l.startswith("\U0001f9e0") and not l.startswith("\u2139")]
        response = "\n".join(lines[-8:]) if lines else "(empty)"
    except subprocess.TimeoutExpired:
        response = "TIMEOUT (120s)"
    except Exception as e:
        response = f"ERR: {e}"

    conn.sendall((response + "\n").encode())

def main():
    conn = connect()
    buf = ""
    while True:
        try:
            data = conn.recv(8192)
            if not data:
                print("[RELAY] Disconnected, reconnecting...", flush=True)
                conn.close()
                conn = connect()
                buf = ""
                continue

            buf += data.decode()
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                if line.startswith("[SERVER]"):
                    continue

                if line.startswith("[") and "] " in line:
                    rest = line.split("] ", 1)[1]
                    if rest.strip():
                        print(f"[RELAY MSG] {line[:120]}", flush=True)
                        threading.Thread(target=respond, args=(conn, rest.strip()), daemon=True).start()

        except Exception as e:
            print(f"[RELAY] Error: {e}, reconnecting...", flush=True)
            try: conn.close()
            except: pass
            conn = connect()
            buf = ""

if __name__ == "__main__":
    main()
