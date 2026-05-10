import http.server, json, sys, subprocess, urllib.request, os, socket

PORT = 17420
TOKEN = "nexus-macmini-hermes-2026"
NEXUS = "http://100.105.185.60:17421/pong"

class ReuseHTTPServer(http.server.HTTPServer):
    allow_reuse_address = True
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        c = int(self.headers.get("Content-Length", 0))
        d = json.loads(self.rfile.read(c))
        if d.get("token") != TOKEN:
            self.send_response(403); self.end_headers(); return

        if self.path == "/ping":
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "host": "mac-mini-neru"}).encode())
        elif self.path == "/exec":
            cmd = d.get("cmd", "")
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                out = (r.stdout + r.stderr)[:3000]
            except subprocess.TimeoutExpired:
                out = "TIMEOUT (60s)"
            self.send_response(200); self.end_headers()
            self.wfile.write(json.dumps({"ok": r.returncode == 0, "out": out}).encode())
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a): pass

os.system("pkill -f receiver.py 2>/dev/null")
os.system("pkill -f receiver-v2.py 2>/dev/null")

urllib.request.urlopen(urllib.request.Request(NEXUS,
    data=json.dumps({"token": TOKEN, "from": "mac-mini", "message": "Receiver v2 ONLINE. /exec gotowy."}).encode(),
    headers={"Content-Type": "application/json"}))

server = ReuseHTTPServer(("0.0.0.0", PORT), H)
server.serve_forever()
