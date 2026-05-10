import http.server, json, subprocess, sys, os, urllib.request, threading, socket, time

PORT = 17420
TOKEN = "nexus-macmini-hermes-2026"
HERMES_CLI = "/Users/nerucb1/.local/bin/hermes"
NEXUS = "http://100.105.185.60:17421/pong"
INBOX = "/tmp/nexus-inbox.jsonl"

def notify_nexus(msg):
    try:
        urllib.request.urlopen(urllib.request.Request(NEXUS,
            data=json.dumps({"token": TOKEN, "from": "mac-mini", "message": msg}).encode(),
            headers={"Content-Type": "application/json"}), timeout=5)
    except: pass

def append_inbox(msg):
    try:
        with open(INBOX, "a") as f:
            f.write(json.dumps({"ts": time.time(), "message": msg}) + "\n")
    except: pass

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        c = int(self.headers.get("Content-Length", 0))
        try:
            d = json.loads(self.rfile.read(c))
        except:
            self.send_response(400); self.end_headers()
            self.wfile.write(json.dumps({"error": "invalid json"}).encode())
            return

        if d.get("token") != TOKEN:
            self.send_response(403); self.end_headers(); return

        if self.path == "/ping":
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "host": "mac-mini-neru", "hermes": os.path.exists(HERMES_CLI)}).encode())

        elif self.path == "/exec":
            cmd = d.get("cmd", "")
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                out = (r.stdout + "\n" + r.stderr)[:5000]
            except subprocess.TimeoutExpired:
                out = "TIMEOUT (60s)"
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "out": out}).encode())

        elif self.path == "/vox":
            prompt = d.get("prompt", "")
            append_inbox(prompt)
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"status": "queued", "to": "Vox"}).encode())
            notify_nexus("QUEUED: wiadomosc przekazana do Voxa. Czekaj na odpowiedz.")

        elif self.path == "/ask":
            prompt = d.get("prompt", "")
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"status": "spawned"}).encode())

            def run_hermes():
                try:
                    full_prompt = f"Odpowiadaj zwiezle po polsku. Jestes Hermes na Mac Mini. Po wykonaniu zadania napisz JEDNOZDANIOWE PODSUMOWANIE.\n\n{prompt}"
                    r = subprocess.run(
                        [HERMES_CLI, "--oneshot", full_prompt, "--yolo"],
                        capture_output=True, text=True, timeout=300,
                        cwd=os.path.expanduser("~"),
                        env={**os.environ, "HOME": os.path.expanduser("~")}
                    )
                    lines = [l.strip() for l in (r.stdout + r.stderr).split("\n") if l.strip() and not l.startswith("\U0001f9e0") and not l.startswith("\u2139")]
                    summary = lines[-1][:400] if lines else "(empty response)"
                    notify_nexus(f"OK: {summary}")
                except subprocess.TimeoutExpired:
                    notify_nexus("TIMEOUT: Hermes nie skonczyl w 300s")
                except Exception as e:
                    notify_nexus(f"FAIL: {str(e)[:200]}")

            threading.Thread(target=run_hermes, daemon=True).start()

        elif self.path == "/check":
            try:
                with open(INBOX) as f:
                    lines = f.readlines()
                count = len(lines)
            except:
                count = 0
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"inbox_count": count}).encode())

        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a): pass

os.system("pkill -f receiver-v 2>/dev/null; sleep 1")
notify_nexus("Receiver v5 ONLINE. /vox -> inbox (Vox czyta), /ask -> oneshot (fallback), /check -> status. Hermes: " + str(os.path.exists(HERMES_CLI)))

class ReuseServer(http.server.HTTPServer):
    allow_reuse_address = True
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

server = ReuseServer(("0.0.0.0", PORT), H)
server.serve_forever()
