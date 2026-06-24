import json
from datetime import datetime

from config import args
from utils import text
from utils import managers
from utils import save_data

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
    response = [
        {
            "material_id":"None",
            "item_id":"None",
            "pokeitem":"None",
            "x":1,
            "y":1,
            "history_id":"None",
            "old_member_savedata_id":"None",
            "pokemon_no":"None",
            "form_no":"None",
            "pokename":"None",
            "pgl_name":"None",
            "nickname":"None",
            "poke_nickname":"None",
            "field_line1":"None",
            "field_line2":"None",
            "field_line3":"None",
            "created_at":"",
            "old_item_id":"None",
            "new_item_id":"None",
            "old_item_name":"None"
        }
    ]
    return json.dumps(response).encode()