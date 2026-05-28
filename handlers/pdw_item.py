#!/usr/bin/env python3
import json
import utility
from config import args

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
        if args.game_sync:
            item_list = utility.read_entralink_data("items")
            for item in item_list:
                item["pokeitem"] = utility.lookup_str("item", item["pokeitem_id"])
            return json.dumps({"cnt": len(item_list), "list": item_list}).encode()

        else:
            return b'{}'

    if item_kind_id == 0:
        item_list = utility.chest.data["list"]
    elif item_kind_id == 1:
        item_list = [item for item in utility.chest.data["list"] if item["pokeitem_id"] in range(149, 213)]

    if sort_key == 1:
        item_list = sorted(item_list, key=lambda x: utility.date_to_unix(x["date"]), reverse=True)
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

    return json.dumps({"cnt": len(utility.chest.data["list"]), "list": item_list}).encode()

# ---------------------
# POST API calls
# ---------------------

def POST_item_delivery_update(_query):

    item_list = []
    for k, item_pair in _query.items():
        if not k.startswith("item_id"):
            continue

        item_id, item_count = item_pair.split("_")
        item_list.append(
                {
                "pokeitem_id":int(item_id),
                "item_cnt":int(item_count)
                }
            )
        utility.chest.remove_item(int(item_id), int(item_count))

    if args.game_sync:
        utility.write_entralink_data(item_list, "items")

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