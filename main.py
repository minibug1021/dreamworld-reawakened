#!/usr/bin/env python3
from pathlib import Path

from api.server import run
from config import args

from utils import save_data
from utils import managers

ROOT_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":

    if args.game_sync:
        save_data.update_gamesync_status(save_data.PlayerStatus.DREAMING)

    managers.crops.update_json()
    managers.chest.update_json()

    managers.crops.process_berry_growth()

    run(port=8080, debug=args.debug)