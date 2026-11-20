#!/usr/bin/env python3
from pathlib import Path

from api.server import run
from config import args

from utils import managers

ROOT_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":

    managers.CheckMemberID()

    managers.crops.update_json()
    managers.chest.update_json()

    managers.crops.process_berry_growth()
    managers.crops.do_garden_expansion()
    managers.RemainsWaterInt()

    run(port=8080, debug=args.debug)