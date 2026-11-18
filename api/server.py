"""The Flask app.

It serves the ?p=<endpoint> API (api/routes.py), Trainer Club sign-up
(api/signup.py), and the mirrored site assets with their patches (utils/assets.py).
"""
import atexit
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs

from flask import Blueprint, Flask, Response, current_app, redirect, request
from werkzeug.wrappers import Response as WerkzeugResponse

from api.routes import HANDLERS, Query, load_handlers
from api.signup import signup
from config import get_secret_key
from game_sync_server.entralinked.utility.db_manager import db
from utils.account_manager import accounts
from utils.assets import SITE_DIR, not_found, path_inside, resolve_static, serve_file
from utils.patching import SWF_PATHS, get_patched_swf

# Copied from a real pdw1.pokemon-gl.com /api/ response
NO_CACHE_HEADERS = {
    "Expires": "Thu, 19 Nov 1981 08:52:00 GMT",
    "Cache-Control": "no-store, no-cache, must-revalidate, post-check=0, pre-check=0",
    "Pragma": "no-cache",
}

site = Blueprint("site", __name__)


# ---------------
# Before every request
# ---------------

@site.before_app_request
def rewrite_incoming_path() -> WerkzeugResponse | None:
    """Enforce a trailing slash on paths that map to a site directory."""
    path = request.path
    site_path = path_inside(SITE_DIR, path.lstrip("/"))
    if not path.endswith("/") and site_path and site_path.is_dir():
        return redirect(f"{path}/", 301)
    return None


# ---------------
# The ?p=<endpoint> API
# ---------------

def _params(data: str) -> Query:
    return {name: values[0] for name, values in parse_qs(data, strict_parsing=True).items()}


def _call_api(method: str, query: Query) -> Response:
    api_name = query.get("p")
    logged_query = {name: "***" if "password" in name else value for name, value in query.items()}
    current_app.logger.info("API %s: %s %s", method, api_name, logged_query)

    handler = HANDLERS[method].get(api_name or "")
    if handler is None:
        current_app.logger.warning("Unknown API: %s %s", method, api_name)
        return Response("{}", status=501, content_type="application/json; charset=utf-8")

    return Response(json.dumps(handler(query)), content_type="application/json; charset=utf-8", headers=NO_CACHE_HEADERS)


@site.get("/api/")
def api_get() -> Response:
    """Handle an API call with its parameters in the query string."""
    return _call_api("GET", _params(request.query_string.decode()))


@site.post("/api/")
def api_post() -> Response:
    """Handle an API call with parameters in the query string and the form body."""
    return _call_api("POST", {**_params(request.query_string.decode()), **_params(request.get_data(as_text=True))})


# ---------------
# Site files
# ---------------

@site.route("/", defaults={"path": ""})
@site.route("/<path:path>")
def catch_all(path: str) -> Response:
    """Serve a patched SWF, a site directory's page, or a static asset for any other path."""
    path = path.split("&")[0]
    full_path = f"/{path}"

    # return patched SWFs from our cache
    filename = Path(path).name
    if filename in SWF_PATHS:
        return Response(get_patched_swf(filename), content_type="application/x-shockwave-flash")

    # find first HTML file inside given directory
    dir_path = path_inside(SITE_DIR, path)
    if dir_path and dir_path.is_dir():
        index = min(dir_path.glob("*.html"), default=None)
        if index is None:
            return not_found(full_path)
        return serve_file(index)

    # static asset
    file_path = resolve_static(full_path)
    if file_path is None:
        return not_found(full_path)

    return serve_file(file_path)


# ---------------
# App
# ---------------

def create_app() -> Flask:
    """Create the Flask app."""
    load_handlers()

    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG if logging.getLogger().isEnabledFor(logging.DEBUG) else logging.INFO)
    app.secret_key = get_secret_key()
    app.register_blueprint(signup)
    app.register_blueprint(site)

    @app.teardown_appcontext
    def close_connections(_exc: BaseException | None) -> None:
        # close the request thread's connections
        db.close()
        accounts.close()

    atexit.register(db.close)
    atexit.register(accounts.close)
    return app
