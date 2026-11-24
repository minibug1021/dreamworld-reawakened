"""The countries in the site's areas.js."""
import json
import re
from functools import cache

from config import ROOT_DIR

AREAS_JS = ROOT_DIR / "dreamworld_assets" / "shared.pokemon-gl.com" / "report" / "assets" / "js" / "areas.js"


@cache
def _entries() -> list[dict]:
    match = re.search(r"var a = (\[.*?\]);", AREAS_JS.read_text(encoding="utf-8"), re.DOTALL)
    if match is None:
        raise ValueError(f"No area list found in {AREAS_JS}")
    quoted = re.sub(r"(?<=[{,])\s*([a-zA-Z_]\w*)\s*:", r'"\1":', match.group(1))
    return json.loads(quoted)


@cache
def by_gts_id() -> dict[int, dict]:
    """Return each country's areas.js entry by its GTS country id."""
    return {entry["gts"]: entry for entry in _entries() if entry["gts"] not in (0, None)}


@cache
def _codes_by_pgl_id() -> dict[int, str]:
    return {entry["pgl"]: entry["iso3166"] for entry in _entries() if entry["pgl"] is not None}


def country_code(pgl_country_id: int | None) -> str | None:
    """Return the three-letter ISO 3166 code of a PGL country id."""
    return _codes_by_pgl_id().get(pgl_country_id) if pgl_country_id is not None else None
