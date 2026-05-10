#!/usr/bin/env python3
"""Hermes Relay Client - laczy Hermesa do relayu, obsluguje dwukierunkowo"""
import socket, subprocess, threading, os, sys

RELAY_HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
RELAY_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 17426
NAME = sys.argv[3] if len(sys.argv) > 3 else "MAC-MINI-HERMES"
HERMES = "/Users/nerucb1/.local/bin/hermes"

def read_from_relay(conn):
    """Czyta z relayu i wypisuje"""
    buf = ""
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            text = data.decode()
            print(text, end="", flush=True)
        except:
            break

def main():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((RELAY_HOST, RELAY_PORT))
    conn.sendall((NAME + "\n").encode())
    print(f"[CONNECTED to relay as {NAME}]")
    print("[Reading relay... type messages and press Enter]")
    
    reader = threading.Thread(target=read_from_relay, args=(conn,), daemon=True)
    reader.start()
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            if line == "/quit":
                break
            if line.startswith("/ask "):
                prompt = line[5:]
                r = subprocess.run([HERMES, "--oneshot", prompt, "--yolo"],
                    capture_output=True, text=True, timeout=60,
                    cwd=os.path.expanduser("~"))
                lines = [l.strip() for l in (r.stdout + r.stderr).split("\n")
                         if l.strip() and not l.startswith("\U0001f9e0") and not l.startswith("\u2139")]
                response = " ".join(lines[-3:])[:500]
                conn.sendall((response + "\n").encode())
            else:
                conn.sendall((line + "\n").encode())
    except KeyboardInterrupt:
        pass
    finally:
        conn.sendall(b"/quit\n")
        conn.close()

if __name__ == "__main__":
    main()
