"""Serves and patches the mirrored site files in dreamworld_assets/."""
import mimetypes
import os
import re
from pathlib import Path

from flask import Response, current_app

from config import LANG, ROOT_DIR, SUPPORTED_LANGUAGES
from utils.patching import apply_substitutions

ASSETS_DIR = ROOT_DIR / "dreamworld_assets"
SITE_DIR   = ASSETS_DIR / f"{LANG}.pokemon-gl.com"
SHARED_DIR = ASSETS_DIR / "shared.pokemon-gl.com"
HOST_MIRRORS = ("assets.pokemon.com", "www.pokemon.com")
_LANG_SEGMENT = re.compile(rf"/({'|'.join(SUPPORTED_LANGUAGES)})/")

# Text files get apply_substitutions before serving. Binary assets (images, fonts, etc.)
# are served as-is.
PATCHABLE_EXTENSIONS = {".js", ".html", ".css"}


def read_and_patch(file_path: Path) -> bytes:
    """Return the file's contents, with the text patches applied if it's a patchable type."""
    data = file_path.read_bytes()

    if file_path.suffix.lower() in PATCHABLE_EXTENSIONS:
        data = apply_substitutions(data, file_path.name)

    return data


def serve_file(file_path: Path) -> Response:
    """Return a response with the patched file and a content type guessed from its name."""
    content_type, _ = mimetypes.guess_type(file_path)
    return Response(read_and_patch(file_path), content_type=content_type or "application/octet-stream")


def not_found(path: str) -> Response:
    """Log and return a 404 response."""
    current_app.logger.info("404 %s", path)
    return Response("Error: Not found", status=404, content_type="text/html")


def path_inside(base: Path, relative: str) -> Path | None:
    """Return base / relative, or None if that would escape base (e.g. through ..)."""
    path = Path(os.path.normpath(base / relative))
    return path if path.is_relative_to(base) else None


def find_file(path: Path | None) -> Path | None:
    """Return path if it's a file, else a file in the same directory whose name matches ignoring case.

    Some files are cased differently on the backend vs. what the game requests.
    """
    if path is None:
        return None
    if path.is_file():
        return path
    if not path.parent.is_dir():
        return None

    name = path.name.lower()
    for candidate in path.parent.iterdir():
        if candidate.name.lower() == name and candidate.is_file():
            return candidate

    return None


def resolve_static(path: str) -> Path | None:
    """Return the file for a static asset URL.

    Look in a host mirror, else the site directory, else the shared directory. Return
    None if there's no such file.
    """
    relative = path.lstrip("/")

    if relative.startswith(tuple(f"{host}/" for host in HOST_MIRRORS)):
        host_path = path_inside(ASSETS_DIR, relative)
        if host_path and host_path.is_file():
            return host_path
        if host_path and host_path.is_dir():
            return host_path / "index.html"

    site_path = find_file(path_inside(SITE_DIR, relative))
    if site_path:
        return site_path

    # the shared mirror has no language prefix (e.g. /en/ -> /)
    return find_file(path_inside(SHARED_DIR, _LANG_SEGMENT.sub("/", relative)))
