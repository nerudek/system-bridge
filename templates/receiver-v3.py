import http.server, json, subprocess, sys, os, urllib.request, tempfile, threading, socket

PORT = 17420
TOKEN = "nexus-macmini-hermes-2026"
HERMES_CLI = "/Users/nerucb1/.local/bin/hermes"
NEXUS = "http://100.105.185.60:17421/pong"

def notify_nexus(msg):
    try:
        urllib.request.urlopen(urllib.request.Request(NEXUS,
            data=json.dumps({"token": TOKEN, "from": "mac-mini", "message": msg}).encode(),
            headers={"Content-Type": "application/json"}), timeout=5)
    except: pass

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        c = int(self.headers.get("Content-Length", 0))
        d = json.loads(self.rfile.read(c))
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

        elif self.path == "/ask":
            prompt = d.get("prompt", "")
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"status": "spawned"}).encode())

            def run_hermes():
                try:
                    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                    tf.write(f"Odpowiadaj zwiezle po polsku.\n\n{prompt}\n\nPo wykonaniu: napisz JEDNOZDANIOWE podsumowanie co zrobiles.")
                    tf.close()
                    r = subprocess.run(
                        [HERMES_CLI, "--prompt-file", tf.name],
                        capture_output=True, text=True, timeout=300,
                        cwd=os.path.expanduser("~")
                    )
                    os.unlink(tf.name)
                    summary = (r.stdout[-500:] + r.stderr[-200:]).strip().replace('\n', ' | ')[:500]
                    notify_nexus(f"OK: {summary}" if r.returncode == 0 else f"ERR({r.returncode}): {summary}")
                except Exception as e:
                    notify_nexus(f"FAIL: {str(e)[:200]}")

            threading.Thread(target=run_hermes, daemon=True).start()

        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a): pass

os.system("pkill -f hermes-receiver.py 2>/dev/null; sleep 1")
notify_nexus("Receiver v3 ONLINE. /ask gotowy (Hermes CLI found: " + str(os.path.exists(HERMES_CLI)) + ")")

class ReuseServer(http.server.HTTPServer):
    allow_reuse_address = True
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

server = ReuseServer(("0.0.0.0", PORT), H)
server.serve_forever()
