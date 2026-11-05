"""Loader for the static game data in json_data/."""
import json
from typing import Any

from config import ROOT_DIR

JSON_DATA_DIR = ROOT_DIR / "json_data"


def load_json_data(name: str) -> Any:
    """Return the parsed contents of json_data/<name>.json."""
    return json.loads((JSON_DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
