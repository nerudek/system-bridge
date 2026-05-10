#!/usr/bin/env python3
"""Vox Relay Writer — wysyla pojedyncza wiadomosc do relayu i rozlacza sie.
Dla Voxa/DeepSeek ktory nie moze utrzymywac stalego polaczenia TCP.
Alternatywa dla relay-client-v2 (ktory jest demonem)."""
import socket, sys

msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()
if not msg:
    print("Usage: relay-say <message>")
    sys.exit(1)

conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn.connect(("127.0.0.1", 17426))
conn.sendall(("VOX\n" + msg + "\n/quit\n").encode())
conn.close()
print("SENT")
