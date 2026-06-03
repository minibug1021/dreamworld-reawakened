import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

parser = argparse.ArgumentParser(description="Dream World HTTP server")
parser.add_argument("--debug", action="store_true")

args = parser.parse_args()

args.game_sync = False
if (ROOT_DIR / "save_data" / "game_sync.json").exists():
    args.game_sync = True