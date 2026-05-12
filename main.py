#!/usr/bin/env python3
import json
import time
import argparse
import threading
from pathlib import Path
from urllib.parse import quote, unquote, parse_qs, urlencode

from server import run

import game_data

ROOT_DIR = Path(__file__).resolve().parent

def process_berry_growth() -> None:
    while True:
        game_data.crops.process_berry_growth()
        time.sleep(3600)

def inject_htm_playerdata() -> None:
    """Inject player_data.json into Dream_Park.htm so it displays the correct information on the UI."""
    
    with open(ROOT_DIR / "save_data" / "player_data.json") as f:
        player_data = json.load(f)

    htm_file = ROOT_DIR / "DreamWorld_data" / "Dream_Park.htm"

    htm_data = bs(htm_file.read_text(), "html.parser")
    
    # entire player_data package
    flashvars_param = htm_data.find_all("param", attrs={"name": "flashvars"})[1]
    
    flashvars = unquote(flashvars_param.get("value"))
    flashvars = parse_qs(flashvars)
    flashvars["json"] = [json.dumps(player_data)]
    flashvars = urlencode(flashvars, doseq=True)

    flashvars_param["value"] = quote(flashvars)

    username_tag = htm_data.find("span", attrs={"id": "header-pglname"}).find_next("span")
    rom_name_tag = htm_data.find("span", attrs={"id": "header-romname"}).find_next("span")

    # username
    username_tag.string = player_data["member"]["pgl_name"]

    # rom name
    rom_name_tag.string = player_data["member"]["rom_name"]

    # profile picture
    pfp_tag = htm_data.find("div", attrs={"class": "logged-in"}).find_next("img")
    pfp_tag.attrs["src"] = f"Dream_Park_files/{player_data['member']['avator_id']}.png"

    htm_file.write_text(str(htm_data))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dream Park HTTP server")
    parser.add_argument("port", nargs="?", type=int, default=8080)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--random", action="store_true", default=False)
    parser.add_argument("--run-webpage", action='store_true', default=False)
    args = parser.parse_args()

    if args.run_webpage:
        from bs4 import BeautifulSoup as bs
        inject_htm_playerdata()

    threading.Thread(target=process_berry_growth, daemon=True).start()
    
    run(port=args.port, debug=args.debug, is_random=args.random)