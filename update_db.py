import json
import time
from pathlib import Path
from config import args
from datetime import datetime
from game_sync_server.entralinked.utility.db_manager import db

def main_update():
    db.update_table()



if __name__ == "__main__":
    main_update()