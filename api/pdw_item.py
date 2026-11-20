import json
from datetime import datetime
from pathlib import Path
from config import args
from utils import text
from utils import managers
from utils import save_data
from flask import request
from api import pdw_item
from api import pdw_home
from game_sync_server.entralinked.utility.db_manager import db

ROOT_DIR = Path(__file__).resolve().parent.parent

with open(ROOT_DIR / "json_data" / "items.json", encoding="UTF-8") as f:
    item_info = json.load(f)

with open(ROOT_DIR / "json_data" / "berries.json", encoding="UTF-8") as f:
    berry_data = json.load(f)

def date_to_unix(datetime_string: str):
    return datetime.strptime(datetime_string, "%Y-%m-%d").timestamp()

# ---------------------
# GET API calls
# ---------------------

def GET_item_list(_query):
    """Returns a filtered/sorted/paginated list of the player's items.

    Args:
        _query: A dict of request parameters. Possible params:
            item_kind_id: Filters the item list by category.
                0 returns all items (default).
                1 returns only berries.
            sort_key: Determines the sort order of the results.
                1 sorts by acquisition date, descending.
                2 sorts by type (bunrui_no, then b_hozon_sentou).
                3 sorts alphabetically by item name (default).
            offset: Number of items to skip for pagination.
                Defaults to 0.
            rowcount: Maximum number of items to return.
                Defaults to 9999.
            status: If set to 2, returns the list of items
                being sent to the Entralink. Defaults to 0.

    Returns:
        A JSON-encoded bytes object. 'cnt' is the total number of
        items before filtering.
    """

    item_kind_id = int(_query.get("item_kind_id", 0))
    sort_key     = int(_query.get("sort_key", 3))
    offset       = int(_query.get("offset", 0))
    rowcount     = int(_query.get("rowcount", 9999))
    status       = int(_query.get("status", 0))

    if status == 2:
        item_list = save_data.read_entralink_data()["items"]
        for item in item_list:
            item["pokeitem"] = text.lookup_str("item", item["pokeitem_id"])
        return json.dumps({"cnt": len(item_list), "list": item_list}).encode()

    if item_kind_id == 0:
        item_list = managers.chest.data["list"]
    elif item_kind_id == 1:
        item_list = [item for item in managers.chest.data["list"] if item["pokeitem_id"] in range(149, 213)]

    if sort_key == 1:
        item_list = sorted(item_list, key=lambda x: date_to_unix(x["date"]), reverse=True)
    elif sort_key == 2:
        item_list = sorted(
            item_list,
            key=lambda x: (
                x["bunrui_no"],
                x["b_hozon_sentou"]
            )
        )
    elif sort_key == 3:
        item_list = sorted(item_list, key=lambda x: x["pokeitem"])

    item_list = item_list[offset:offset+rowcount]

    return json.dumps({"cnt": len(managers.chest.data["list"]), "list": item_list}).encode()

def GET_item_return_update(_query):
    material_id = request.args.get("material_id")

    x = request.args.get("x")

    y = request.args.get("y")

    share_result = managers.share.share_to_chest(material_id)

    item_id = share_result["pokeitem_id"]

    managers.chest.add_item(item_id, 1)

    result = managers.share.data["share_list"]

    return json.dumps(result).encode()
 
def GET_item_exhibit_update(_query):
    x = int(_query.get("x"))

    y = int(_query.get("y"))

    item_id = int(_query.get("item_id"))

    place_result = managers.share.place( x, y, item_id)

    managers.chest.remove_item(item_id, 1)

    result = managers.share.data["share_list"]

    return json.dumps(result).encode()

def GET_item_trade_update(_query):
    almost_material_id = int(_query.get("other_material_id"))

    material_id = json.dumps(almost_material_id)

    other_member_savedata_id = int(_query.get("other_member_id"))

    member_id = other_member_savedata_id

    member_savedata_id = db.read(save_data.gscd, "member_id")

    item_id = int(_query.get("item_id"))

    print(other_member_savedata_id)

    if other_member_savedata_id == member_savedata_id:
        swap_result = managers.share.switch_swap(material_id, member_savedata_id, item_id)
    else:
        swap_result = switch_swap(material_id, member_savedata_id, item_id, member_id)

    old_item_id = swap_result["old_item_id"]

    managers.chest.remove_item(item_id, 1)

    managers.chest.add_item(old_item_id, 1)

    if other_member_savedata_id == member_savedata_id:
        result = managers.share.data["share_list"]
    else:
        pdw_home.swapped_footprint_plot(member_id)
        s_data = db.f_read(member_id, "share_data")
        result = s_data["share_list"]

    return json.dumps(result).encode()

def GET_friend_trade_list(_query):
    global member_id

    member_id = int(_query.get("other_member_savedata_id"))

    print(member_id)

    s_data = db.f_read(member_id, "share_data")

    response = s_data["share_list"]

    return json.dumps(response).encode()

# ---------------------
# POST API calls
# ---------------------

def POST_item_delivery_update(_query):
    print(json.dumps(_query, indent=2))

    # Build the new queue from the request
    new_queue = {}
    for k, item_pair in _query.items():
        if not k.startswith("item_id"):
            continue
        item_id, item_count = item_pair.split("_")
        new_queue[int(item_id)] = int(item_count)

    # Build the old queue from whatever is currently staged
    old_queue = {
        item["pokeitem_id"]: item["item_cnt"]
        for item in save_data.read_entralink_data().get("items", [])
    }

    # Determine the delta to add/subtract Chest items
    all_ids = set(new_queue) | set(old_queue)
    for item_id in all_ids:
        delta = new_queue.get(item_id, 0) - old_queue.get(item_id, 0)
        if delta > 0:
            managers.chest.remove_item(item_id, delta)
        elif delta < 0:
            managers.chest.add_item(item_id, -delta)

    # Save the new queue state
    item_list = [
        {"pokeitem_id": item_id, "item_cnt": item_cnt}
        for item_id, item_cnt in new_queue.items()
    ]

    if args.game_sync:
        save_data.write_entralink_data(item_list, "items")

    return b'{}'

def POST_item_trade_list(_query):
    response = managers.share.data["share_list"]

    return json.dumps(response).encode()

# ---------------------
# Friend Share Shelf Code
# ---------------------

def fetch_plot_by_id(material_id: int, member_id: int):
    s_data = db.f_read(member_id, "share_data")
    return next((p for p in s_data["share_list"] if p["material_id"] == material_id), None)

def switch_swap(material_id: int, member_savedata_id: int, item_id: int, member_id: int):
    s_data = db.f_read(member_id, "share_data")

    plot = fetch_plot_by_id(material_id, member_id)

    plot_index = s_data["share_list"].index(plot)

    old_item_id = plot["item_id"]

    item_desc = text.lookup_str("item_descriptions", item_id)

    pgl_name = save_data.read_player_data()["member"]["pgl_name"]

    player_name = save_data.read_player_data()["member"]["player_name"]

    pokemon_name = save_data.read_player_data()["member"]["pokemon_name"]

    pokemon_no = save_data.read_sleeping_pokemon()["pokemon_no"]

    pokemon_nickname = save_data.read_sleeping_pokemon()["pokemon_nickname"]

    form_no = save_data.read_sleeping_pokemon()["form_no"]

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    switch_swap_data = {
        "item_id": item_id,
        "old_item_id": old_item_id,
        "count": 1
    }

    s_data["share_list"][plot_index] = {"material_id": material_id, "item_id": item_id, "pokeitem": text.lookup_str("item", item_id), "x": plot["x"], "y": plot["y"], "history_id": "" , "old_member_savedata_id": member_savedata_id, "pokemon_no": pokemon_no, "form_no": form_no, "pokename": pokemon_name, "pgl_name": pgl_name, "nickname": player_name, "poke_nickname": pokemon_nickname, "field_line1": item_desc[0], "field_line2": item_desc[1], "field_line3": item_desc[2], "created_at": current_time, "old_item_id": old_item_id, "new_item_id": item_id , "old_item_name": text.lookup_str("item", old_item_id)}

    redundant_fields = {"kinomi", "kinomi_id"}
    share_data = {
        "cnt": len(s_data["share_list"]),
        "share_list": [
            {k: v for k, v in item.items() if k not in redundant_fields}
            for item in s_data["share_list"]
        ]
    }

    db.f_write(member_id, "share_data", share_data)

    return switch_swap_data