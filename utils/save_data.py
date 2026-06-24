import time
from typing import List
from pathlib import Path
from random import randint
from enum import Enum, auto

from game_sync_server.entralinked.utility.db_manager import db

ROOT_DIR = Path(__file__).resolve().parent.parent
_GSCD_PATH = ROOT_DIR / "save_data" / "gscd.txt"

def _load_gscd() -> str:
    _GSCD_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _GSCD_PATH.exists():
        _GSCD_PATH.write_text("")
    return _GSCD_PATH.read_text().strip()

gscd = _load_gscd()

class PlayerStatus(Enum):
    AWAKE = 0
    SLEEPING = auto()
    DREAMING = auto()
    WAKE_READY = auto()

def generate_otoken():
    world_id = read_player_data()["member"]["world_id"]
    return f"{randint(1, 99)}dwt{world_id}{int(time.time()):x}.{randint(10000000, 99999999)}"

# player data

def read_player_data(game_sync_id: str = None) -> dict:
    return db.read(game_sync_id or gscd, "player_data") or {}

def write_player_data(data: dict, game_sync_id: str = None):
    player_data = read_player_data(game_sync_id)
    player_data.setdefault("member", {}).update(data)
    db.write(game_sync_id or gscd, "player_data", player_data)

# game sync data

def read_entralink_data() -> dict:
    return db.read(gscd, "game_sync") or {}

def write_entralink_data(data: List[dict], data_type: str):
    game_sync = db.read(gscd, "game_sync") or {}
    game_sync[data_type] = data
    db.write(gscd, "game_sync", game_sync)

def update_gamesync_status(status: PlayerStatus):
    if not db.read(gscd, "game_sync"):
        raise ValueError("A sleeping Pokémon must be tucked to bed first.")

    write_player_data({"play_status": status.value})