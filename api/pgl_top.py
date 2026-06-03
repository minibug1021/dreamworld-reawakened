import json

from utils import save_data

# ---------------------
# GET API calls
# ---------------------

def GET_init(_query):
    return json.dumps(save_data.read_player_data()).encode()

# ---------------------
# POST API calls
# ---------------------
