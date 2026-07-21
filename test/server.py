import http.server
import json
import os
import sys
import urllib.request
import urllib.error


BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000").rstrip("/")


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    """前端静态文件服务 + API 反向代理"""

    # ==================== HTTP 方法分发 ====================

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

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    # ==================== CORS 头 ====================

    def _set_cors_headers(self):
        """设置 CORS 跨域响应头"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    # ==================== 反向代理核心 ====================

    def _proxy_request(self, method):
        """将 API 请求反向代理到后端服务"""
        backend_url = f"{BACKEND_URL}{self.path}"

        # 读取请求体
        body = None
        content_length = self.headers.get("Content-Length")
        if content_length:
            try:
                body = self.rfile.read(int(content_length))
            except (ValueError, OSError):
                pass

        # 构建代理请求（转发关键请求头）
        forward_headers = {
            "Content-Type": self.headers.get("Content-Type", "application/json"),
            "Accept": self.headers.get("Accept", "application/json"),
            "X-Forwarded-For": self.headers.get("X-Forwarded-For", self.client_address[0]),
            "X-Forwarded-Host": self.headers.get("Host", ""),
        }
        # 转发 Content-Length（仅在有 body 时设置，避免 urllib 自动计算冲突）
        if body:
            forward_headers["Content-Length"] = str(len(body))

        req = urllib.request.Request(
            backend_url,
            data=body,
            headers=forward_headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                self._set_cors_headers()
                # 复制后端响应头（排除传输层编码，由我们自行控制）
                for key, value in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                        self.send_header(key, value)
                data = resp.read()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            # 后端返回的 4xx/5xx 正常透传
            self.send_response(e.code)
            self._set_cors_headers()
            data = e.read()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.URLError as e:
            # 后端不可达（网络/连接错误）
            self.send_response(502)
            self._set_cors_headers()
            msg = json.dumps({"detail": f"Backend unavailable: {BACKEND_URL}", "error": str(e.reason)}).encode()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    # ==================== 静态文件服务 ====================

    def _serve_static(self):
        """提供静态文件 + SPA 路由回退"""
        file_path = self.translate_path(self.path)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.path = "/"
        return super().do_GET()

    # ==================== 日志 ====================

    def log_message(self, format, *args):
        """输出结构化日志，便于排查问题"""
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.command} {self.path} - {args[0] if args else ''}\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    directory = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/nginx/html"
    os.chdir(directory)
    server = http.server.HTTPServer(("0.0.0.0", port), ProxyHandler)
    print(f"Serving {directory} on port {port}, backend: {BACKEND_URL}")
    server.serve_forever()