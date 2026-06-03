from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs, urlencode
from html import escape
from enum import StrEnum

import logging
from pathlib import Path

from api.routes import (
    GET_RESPONSES,
    POST_RESPONSES
)

from utils import language
from utils.swf import build_swf_params

# ---------------
# Request handler
# ---------------

ROOT_DIR = Path(__file__).resolve().parent.parent

class ANSIColor(StrEnum):
    RED = "\033[31m"
    RESET = "\033[0m"

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)

        if "404" in message:
            return f"{ANSIColor.RED}{message}{ANSIColor.RESET}"

        return message

class S(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        logging.info("%s - - %s", self.address_string(), format % args)

    def _dispatch_api(self, api_name, query, api_map):
        """Look up api_name in the dispatch tables and write the response."""

        if api_name in api_map:
            body = api_map[api_name](query)
        else:
            logging.warning("Unknown API: %s", api_name)
            self.send_response(501)
            self.end_headers()
            self.wfile.write(b"{}")
            return

        self.send_response(200)
        #disable caching
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
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

        if path.endswith("main.swf") and not parsed.query:
            url_params = build_swf_params()
            query_string = urlencode(url_params)
            redirect_url = f"{path}?{query_string}"

            self.send_response(302)
            self.send_header("Location", redirect_url)
            self.end_headers()
            return

        if path == "/api/":
            query = {k: v[0] for k, v in parse_qs(parsed.query, strict_parsing=True).items()}
            api_name = query["p"]
            logging.info("API GET: %s", api_name)
            self._dispatch_api(api_name, query, GET_RESPONSES)
            return

        if path == "/":
            with open(ROOT_DIR / "DreamWorld_data" / "Dream_Park.htm", "rb") as f:
                data = f.read()
                data = data.replace(b"%%LANG%%", language.player_language.encode())

            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if not path.startswith("/DreamWorld_data/"):
            file_path = ROOT_DIR / "DreamWorld_data" / path.lstrip("/")
        else:
            file_path = ROOT_DIR / path.lstrip("/")

        if file_path.is_file():
            self._log_referrer(file_path)

            with open(file_path, "rb") as f:
                data = f.read()

            if file_path.name == "swfembed2.js":
                data = data.replace(
                    b"lang:window.location",
                    f"lang:'http://{language.player_language}.pokemon-gl.com/'".encode()
                )

            data = data.replace(b"cdn2.pokemon-gl.com", b"DreamWorld_data")

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
        query = {k: v[0] for k, v in parse_qs(post_data.decode(encoding="UTF-8"), strict_parsing=True).items()}
        api_name = query["p"]

        logging.info("API POST: %s", api_name)

        self._log_referrer(f"POST:{api_name}")
        self._dispatch_api(api_name, query, POST_RESPONSES)

# ------------
# Server start
# ------------

def run(server_class=HTTPServer, handler_class=S, port=8080, debug=False):

    server_address = ("127.0.0.1", port)
    httpd = server_class(server_address, handler_class)

    httpd.app_config = {
        "debug": debug
    }

    log_level = logging.DEBUG if httpd.app_config["debug"] else logging.INFO

    console_handler = logging.StreamHandler()
    log_format = "%(asctime)s - %(levelname)s - %(message)s" if debug else "%(message)s"
    console_handler.setFormatter(ColoredFormatter(log_format))

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(console_handler)

    logging.info("Server started!%s\n", " (debug mode)" if debug else "")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()

    logging.info("Stopping server...\n")