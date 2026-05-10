#!/usr/bin/env python3
import json
import time
from pathlib import Path
from random import choice
from random import randint
from datetime import datetime

# --------------------
# Pokemon related data
# --------------------

ROOT_DIR = Path(__file__).resolve().parent

# --- save data ---

with open(ROOT_DIR / "save_data" / "player_data.json", encoding="UTF-8") as f:
    player_data = json.load(f)

with open(ROOT_DIR / "save_data" / "crop_data.json", encoding="UTF-8") as f:
    crop_data = json.load(f)

with open(ROOT_DIR / "save_data" / "chest_data.json", encoding="UTF-8") as f:
    chest_data = json.load(f)

# --- helper data ---

with open(ROOT_DIR / "json_data" / "items.json", encoding="UTF-8") as f:
    item_info = json.load(f)

with open(ROOT_DIR / "json_data" / "pokemon.json", encoding="UTF-8") as f:
    pokemon_info = json.load(f)

with open(ROOT_DIR / "json_data" / "area_data.json", encoding="UTF-8") as f:
    area_info = json.load(f)

pokemon_natures = ("Adamant","Bashful","Bold","Brave","Calm","Careful","Docile","Gentle","Hardy","Hasty","Impish","Jolly","Lax","Lonely","Mild","Modest","Naive","Naughty","Quiet","Quirky","Rash","Relaxed","Sassy","Serious","Timid")

# --------------------
# Helper functions
# --------------------

def generate_otoken():
    return f"{randint(1, 99)}dwt{player_data['member']['world_id']}{format(int(time.time()), 'x')}.{randint(10000000, 99999999)}"

def date_to_unix(datetime_string: str):
    return datetime.strptime(datetime_string, "%Y-%m-%d")

def get_random_pokemon() -> dict[str: str|None]:
    pkmn = choice(list(pokemon_info.keys()))
    natdex = pkmn.split("-")[0]

    return {**pokemon_info[pkmn], "pokemon_no": natdex}