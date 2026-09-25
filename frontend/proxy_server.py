from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "dist")
BACKEND = "http://127.0.0.1:8000"


class ProxyHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_request()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_request()
        else:
            self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        if self.path.startswith("/api/"):
            self.proxy_request()
        else:
            self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self.proxy_request()
        else:
            self.send_error(405, "Method Not Allowed")

    def proxy_request(self):
        target = BACKEND + self.path

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else None

        headers = {}
        for key in ["Content-Type", "Authorization", "Accept"]:
            if self.headers.get(key):
                headers[key] = self.headers[key]

        try:
            request = Request(
                target,
                data=body,
                headers=headers,
                method=self.command
            )

            with urlopen(request, timeout=120) as response:
                data = response.read()

                self.send_response(response.status)

                content_type = response.headers.get("Content-Type")
                if content_type:
                    self.send_header("Content-Type", content_type)

                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        except HTTPError as e:
            data = e.read()

            self.send_response(e.code)
            self.send_header(
                "Content-Type",
                e.headers.get("Content-Type", "application/json")
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        except URLError as e:
            message = f"Backend connection failed: {e}".encode()

            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)


print("MEDIA DNA frontend running on http://localhost:5173")
print("API requests are proxied to http://127.0.0.1:8000")

server = ThreadingHTTPServer(("127.0.0.1", 5173), ProxyHandler)
server.serve_forever()