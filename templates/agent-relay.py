#!/usr/bin/env python3
"""Bidirectional Agent Relay - obie strony moga pisac i czytac na zywo"""
import socket, threading, sys, os, time

PORT = 17426
IDENTITY = "MAC-MINI"  # zmien na "MACBOOK" na drugiej maszynie

class Relay:
    def __init__(self, port, identity):
        self.port = port
        self.identity = identity
        self.clients = {}
        self.lock = threading.Lock()
    
    def broadcast(self, sender, msg):
        with self.lock:
            for name, conn in list(self.clients.items()):
                if name != sender:
                    try:
                        conn.sendall(f"[{sender}] {msg}\n".encode())
                    except:
                        pass
    
    def handle(self, conn, addr):
        try:
            name = conn.recv(64).decode().strip()
        except:
            name = f"anon-{addr[1]}"
        
        with self.lock:
            self.clients[name] = conn
        
        self.broadcast("SERVER", f"{name} JOINED")
        
        try:
            while True:
                data = conn.recv(8192)
                if not data:
                    break
                msg = data.decode().strip()
                if msg.startswith("/"):
                    cmd = msg[1:].split()[0]
                    if cmd == "quit":
                        break
                    elif cmd == "who":
                        with self.lock:
                            conn.sendall(f"ONLINE: {list(self.clients.keys())}\n".encode())
                    elif cmd == "msg":
                        parts = msg.split(" ", 2)
                        if len(parts) >= 3:
                            target, text = parts[1], parts[2]
                            with self.lock:
                                if target in self.clients:
                                    self.clients[target].sendall(f"[{name}->you] {text}\n".encode())
                    continue
                
                self.broadcast(name, msg)
        except:
            pass
        finally:
            with self.lock:
                if name in self.clients:
                    del self.clients[name]
            self.broadcast("SERVER", f"{name} LEFT")
            try: conn.close()
            except: pass
    
    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.port))
        s.listen(10)
        print(f"[RELAY:{self.identity}] port {self.port}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=self.handle, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    identity = sys.argv[1] if len(sys.argv) > 1 else IDENTITY
    Relay(PORT, identity).start()
