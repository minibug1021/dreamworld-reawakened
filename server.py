#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from html import escape

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

ROOT_DIR = Path(__file__).resolve().parent

class S(BaseHTTPRequestHandler):

    def _dispatch_api(self, api_name, query, static_map, dynamic_map):
        """Look up api_name in the dispatch tables and write the response."""
        
        query["is_random"] = False
        if self.server.app_config["is_random"]:
            query["is_random"] = True

        if api_name in static_map:
            body = static_map[api_name]
        elif api_name in dynamic_map:
            body = dynamic_map[api_name](query)
        else:
            logging.warning("Unknown API: %s", api_name)
            self.send_response(501)
            self.end_headers()
            self.wfile.write(b"")
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)

    def _log_referrer(self, file_path):
        """In debug mode, log the Referer header."""
        if self.server.app_config["debug"]:
            referrer = self.headers.get("Referer", "<no referrer>")
            logging.debug("[DEBUG] File requested: %s  |  Referer: %s", file_path, referrer)

    def do_GET(self):
        logging.info("GET %s", self.path)
        parsed = urlsplit(self.path)
        path = escape(parsed.path)

        if path == "/api/":
            query = parse_qs(parsed.query, strict_parsing=True)
            api_name = query["p"][0]
            logging.info("API GET: %s", api_name)
            self._dispatch_api(api_name, query, STATIC_GET_RESPONSES, DYNAMIC_GET_RESPONSES)
            return

        if path == "/":
            with open(Path(ROOT_DIR / "DreamWorld_data" / "Dream_Park.htm"), "rb") as f:
                data = f.read()
            
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if "flash" not in self.headers.get("User-Agent").lower():
            file_path = ROOT_DIR / "DreamWorld_data" / path.lstrip("/")
        else:
            file_path = ROOT_DIR / path.lstrip("/")
        
        if file_path.is_file():
            self._log_referrer(file_path)
            
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
        
        self._log_referrer(f"POST:{api_name}")
        self._dispatch_api(api_name, query, STATIC_POST_RESPONSES, DYNAMIC_POST_RESPONSES)


# ------------
# Server start
# ------------

def run(server_class=HTTPServer, handler_class=S, port=8080, debug=False, is_random=False):
    
    server_address = ("127.0.0.1", port)
    httpd = server_class(server_address, handler_class)

    httpd.app_config = {
        "debug": debug,
        "is_random": is_random
    }

    log_level = logging.DEBUG if httpd.app_config["debug"] else logging.INFO
    
    logging.basicConfig(level=log_level)
    logging.info("Starting server%s...\n", " (debug mode)" if httpd.app_config["debug"] else "")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    
    httpd.server_close()
    
    logging.info("Stopping server...\n")