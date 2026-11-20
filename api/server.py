"""The Flask app.

It serves the ?p=<endpoint> API (api/routes.py), Trainer Club sign-up
(api/signup.py), and the mirrored site assets with their patches (utils/assets.py).
"""
import atexit
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from flask import Blueprint, Flask, Response, current_app, redirect, request
from werkzeug.wrappers import Response as WerkzeugResponse

from api.routes import HANDLERS, Query, load_handlers
from api.signup import signup
from config import SUPPORTED_LANGUAGES, get_secret_key
from game_sync_server.entralinked.utility.db_manager import db
from utils.account_manager import accounts
from utils.assets import not_found, path_inside, resolve_static, serve_file, site_dir
from utils.language import LANGUAGE_COOKIE, current_language
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
    site_path = path_inside(site_dir(current_language()), path.lstrip("/"))
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
# Language links
# ---------------

LANGUAGE_COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # a year


@site.get("/language/<lang>")
def choose_language(lang: str) -> Response | WerkzeugResponse:
    """Remember the visitor's site language and go back to the page they were on.

    It only goes back to a page on this site. Otherwise it goes to the front page.
    """
    if lang not in SUPPORTED_LANGUAGES:
        return not_found(request.path)
    referrer = urlsplit(request.referrer or "")
    back = "/"
    if referrer.netloc == request.host:
        back = "/" + referrer.path.lstrip("/\\") + (f"?{referrer.query}" if referrer.query else "")
    response = redirect(back)
    response.set_cookie(LANGUAGE_COOKIE, lang, max_age=LANGUAGE_COOKIE_MAX_AGE, samesite="Lax",
                        secure=request.is_secure)
    return response


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
    dir_path = path_inside(site_dir(current_language()), path)
    if dir_path and dir_path.is_dir():
        index = min(dir_path.glob("*.html"), default=None)
        if index is None:
            return not_found(full_path)
        return serve_file(index)

    # static asset
    found = resolve_static(full_path)
    if found is None:
        return not_found(full_path)
    file_path, per_visitor = found
    return serve_file(file_path, per_visitor=per_visitor)


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

    @app.after_request
    def upgrade_insecure_requests(response: Response) -> Response:
        # Force HTTPS everywhere.
        if request.is_secure:
            response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
        return response

    @app.teardown_appcontext
    def close_connections(_exc: BaseException | None) -> None:
        # close the request thread's connections
        db.close()
        accounts.close()

    atexit.register(db.close)
    atexit.register(accounts.close)
    return app
