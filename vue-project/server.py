import http.server
import os
import sys


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # SPA fallback: if file not found, serve index.html
        file_path = self.translate_path(self.path)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.path = '/'
        return super().do_GET()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    directory = sys.argv[2] if len(sys.argv) > 2 else '/usr/share/nginx/html'
    os.chdir(directory)
    server = http.server.HTTPServer(('0.0.0.0', port), SPAHandler)
    print(f'Serving {directory} on port {port}')
    server.serve_forever()