#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import logging
from pathlib import Path

from api_handlers import (
    STATIC_GET_RESPONSES,
    STATIC_POST_RESPONSES,
    DYNAMIC_GET_RESPONSES,
    DYNAMIC_POST_RESPONSES,
)

# ---------------
# Request handler
# ---------------

class S(BaseHTTPRequestHandler):

    def _dispatch_api(self, api_name, query, static_map, dynamic_map):
        """Look up api_name in the dispatch tables and write the response."""
        if api_name in static_map:
            body = static_map[api_name]
        elif api_name in dynamic_map:
            body = dynamic_map[api_name](query)
        else:
            logging.warning("Unknown API: %s", api_name)
            self.send_response(410)
            self.end_headers()
            self.wfile.write(b"")
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        logging.info("GET %s", self.path)
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/api/":
            query = parse_qs(parsed.query, strict_parsing=True)
            api_name = query["p"][0]
            logging.info("API GET: %s", api_name)
            self._dispatch_api(api_name, query, STATIC_GET_RESPONSES, DYNAMIC_GET_RESPONSES)
            return

        if path == "/":
            if self.headers.get("User-Agent") == "Shockwave Flash":
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:8080/src/swf/theme/assets/common/main.swf")
                self.end_headers()
                return

            with open(Path("Dream_Park.htm"), "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # Strip bugged trailing &s that PDW sometimes adds
        if "&" in path:
            path = path.split("&")[0]

        file_path = Path(".") / path.lstrip("/")
        if file_path.is_file():
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Error: Not found")

    def do_POST(self):
        logging.info("POST %s", self.path)
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        query = parse_qs(post_data.decode(), strict_parsing=True)
        api_name = query["p"][0]
        logging.info("API POST: %s", api_name)
        self._dispatch_api(api_name, query, STATIC_POST_RESPONSES, DYNAMIC_POST_RESPONSES)


# ------------
# Server start
# ------------

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('127.0.0.1', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting server...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping server...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()