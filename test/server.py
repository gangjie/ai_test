import http.server
import os
import sys
import urllib.request


BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy_request("GET")
        else:
            self._serve_static()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy_request("POST")
        else:
            self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        if self.path.startswith("/api/"):
            self._proxy_request("PUT")
        else:
            self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self._proxy_request("DELETE")
        else:
            self.send_error(405, "Method Not Allowed")

    def _proxy_request(self, method):
        """Proxy API requests to the backend"""
        backend_url = f"{BACKEND_URL}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else None

        req = urllib.request.Request(
            backend_url,
            data=body,
            headers={
                "Content-Type": self.headers.get("Content-Type", "application/json"),
                "Accept": self.headers.get("Accept", "application/json"),
            },
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                # Copy response headers
                for key, value in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                        self.send_header(key, value)
                data = resp.read()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            data = e.read()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.URLError:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"detail":"Backend unavailable"}')

    def _serve_static(self):
        """Serve static files with SPA fallback"""
        file_path = self.translate_path(self.path)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.path = "/"
        return super().do_GET()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    directory = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/nginx/html"
    os.chdir(directory)
    server = http.server.HTTPServer(("0.0.0.0", port), ProxyHandler)
    print(f"Serving {directory} on port {port}")
    server.serve_forever()