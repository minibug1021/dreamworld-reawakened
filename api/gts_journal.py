import re
import json
from pathlib import Path
from random import choice
from random import randint
from utils import language
from utils.pokemon import get_random_pokemon

ROOT_DIR = Path(__file__).resolve().parent.parent
LANG = language.player_language

def load_areas() -> dict:
    file_path = ROOT_DIR / "dreamworld_assets" / "shared.pokemon-gl.com" / "report" / "assets" / "js" / "areas.js"
    text = open(file_path, encoding="UTF-8").read()

    match = re.search(r"var a = (\[.*?\]);", text, re.DOTALL)
    raw = match.group(1)

    quoted = re.sub(r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*:', r'"\1":', raw)

    areas = json.loads(quoted)
    return {entry["gts"]: entry for entry in areas if entry["gts"] is not None}

# ---------------------
# GET API calls
# ---------------------

def GET_trade_list(_query):

    trade_list = []

    areas = load_areas()

    # Dummy data
    for _ in range(100):
        pkmn_one = get_random_pokemon()
        pkmn_two = get_random_pokemon()

        country_one = choice(list(areas.keys()))
        country_two = choice(list(areas.keys()))

        trade = {
            "trade1": {
            "country_id": country_one,
            "country_name": areas[country_one]["names"][LANG],
            "monsno": pkmn_one["pokemon_no"],
            "form_no": pkmn_one.get("form_no", 0),
            "poke_level": randint(1, 100),
            "sex": choice(pkmn_one["gender_ratio"])
            },

            "trade2": {
            "country_id": country_two,
            "country_name": areas[country_two]["names"][LANG],
            "monsno": pkmn_two["pokemon_no"],
            "form_no": pkmn_two.get("form_no", 0),
            "poke_level": randint(1, 100),
            "sex": choice(pkmn_two["gender_ratio"])
            }
        }

        trade_list.append(trade)

    return json.dumps({"trade_list":trade_list}).encode()

# ---------------------
# POST API calls
# ---------------------
