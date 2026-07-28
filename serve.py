#!/usr/bin/env python3
"""Servidor estático + proxy al backend Django."""
import http.server
import urllib.request
import os

BACKEND = "http://localhost:8000"
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend", "sispoa", "dist", "sispoa")

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/") or self.path.startswith("/media/") or self.path.startswith("/static/"):
            url = f"{BACKEND}{self.path}"
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req) as resp:
                    self.send_response(resp.status)
                    for k, v in resp.headers.items():
                        if k.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                            self.send_header(k, v)
                    # CORS
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.copyfile(resp, self.wfile)
            except Exception as e:
                self.send_error(502, f"Proxy error: {e}")
        else:
            # SPA catch-all: rutas que no son archivos → index.html
            filepath = self.translate_path(self.path)
            if not os.path.isfile(filepath):
                self.path = "/index.html"
            super().do_GET()

    def _proxy_request(self, method):
        if not self.path.startswith("/api/"):
            self.send_error(405)
            return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""
        url = f"{BACKEND}{self.path}"
        try:
            headers = {k: v for k, v in self.headers.items()
                       if k.lower() not in ("host", "connection", "transfer-encoding", "content-length")}
            req = urllib.request.Request(url, data=body or None, headers=headers, method=method)
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                        self.send_header(k, v)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.copyfile(resp, self.wfile)
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")

    def do_POST(self):
        self._proxy_request("POST")

    def do_PATCH(self):
        self._proxy_request("PATCH")

if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    server = http.server.HTTPServer(("0.0.0.0", 4200), ProxyHandler)
    print(f"Sirviendo frontend + proxy API en http://localhost:4200/")
    print(f"  API → {BACKEND}/api/v1/...")
    server.serve_forever()
