from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json
import logging

from patchwork.registry import Registry

logger = logging.getLogger(__name__)


class PatchworkRequestHandler(BaseHTTPRequestHandler):
    registry: Registry = None

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def _handle_request(self):
        parsed = urlparse(self.path)
        path = parsed.path
        method = self.command.upper()

        definition = self.registry.lookup(method, path)

        if definition is None:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            body = json.dumps({"error": "No matching route found", "method": method, "path": path})
            self.wfile.write(body.encode("utf-8"))
            return

        status = definition.get("status", 200)
        headers = definition.get("headers", {})
        body = definition.get("body", "")

        self.send_response(status)

        if isinstance(body, (dict, list)):
            self.send_header("Content-Type", "application/json")
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(json.dumps(body).encode("utf-8"))
        else:
            content_type = headers.pop("Content-Type", "text/plain")
            self.send_header("Content-Type", content_type)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(str(body).encode("utf-8"))

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_PUT(self):
        self._handle_request()

    def do_DELETE(self):
        self._handle_request()

    def do_PATCH(self):
        self._handle_request()


def create_server(registry: Registry, host: str = "127.0.0.1", port: int = 8080) -> HTTPServer:
    handler = type(
        "BoundHandler",
        (PatchworkRequestHandler,),
        {"registry": registry},
    )
    server = HTTPServer((host, port), handler)
    logger.info("Patchwork server created on %s:%d", host, port)
    return server
