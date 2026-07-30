#!/usr/bin/env python3
"""Servidor HTTPS simples para o SisCarEs.

- Serve arquivos estáticos do frontend em /
- Encaminha /api/v1/*, /static/* e /docs* para o backend uvicorn na porta 8000
"""
import http.server
import ssl
import http.client
import os
import urllib.parse
from pathlib import Path

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
HTTPS_PORT = 8443
CERT_FILE = "/root/siscares/backend/certs/cert.pem"
KEY_FILE = "/root/siscares/backend/certs/key.pem"
FRONTEND_DIR = Path("/root/siscares/frontend")


class SisCarEsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def _proxy(self, path):
        headers = {key: value for key, value in self.headers.items()}
        headers["Host"] = f"{BACKEND_HOST}:{BACKEND_PORT}"
        headers.pop("Accept-Encoding", None)

        content_length = int(headers.get("Content-Length", 0))
        body = None
        if content_length:
            body = self.rfile.read(content_length)

        try:
            conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT)
            conn.request(self.command, path, body=body, headers=headers)
            resp = conn.getresponse()

            self.send_response(resp.status, resp.reason)
            for h, v in resp.getheaders():
                if h.lower() in ("transfer-encoding", "connection", "content-encoding"):
                    continue
                self.send_header(h, v)
            self.end_headers()
            self.wfile.write(resp.read())
            conn.close()
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Backend error: {e}".encode())

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/") or parsed.path.startswith("/static/") or parsed.path.startswith("/docs") or parsed.path == "/openapi.json":
            return self._proxy(self.path)
        if parsed.path == "/":
            self.path = "/static/pages/login.html"
        return super().do_GET()

    def do_POST(self):
        return self._proxy(self.path)

    def do_PUT(self):
        return self._proxy(self.path)

    def do_DELETE(self):
        return self._proxy(self.path)

    def do_OPTIONS(self):
        return self._proxy(self.path)


if __name__ == "__main__":
    server_address = ("0.0.0.0", HTTPS_PORT)
    httpd = http.server.HTTPServer(server_address, SisCarEsHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print(f"Servindo SisCarEs em https://0.0.0.0:{HTTPS_PORT}")
    httpd.serve_forever()
