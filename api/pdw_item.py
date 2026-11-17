"""pdw.item.*: the Treasure Chest (pdw_item_list.swf), the items queued for the Entralink, and the Share Shelf."""
import logging
from collections.abc import Callable
from enum import IntEnum
from operator import itemgetter
from typing import Any

from api.routes import Query, endpoint, query_int
from utils import managers, save_data, text, visits
from utils.berries import is_berry
from utils.models import ChestItem, EntralinkItem, ShareSlot

logger = logging.getLogger(__name__)


class ItemKind(IntEnum):
    """item_kind_id: which items item_list shows."""

    ALL = 0
    BERRIES = 1


ENTRALINK_QUEUE_STATUS = 2  # status: list the Entralink queue instead of the chest
DEFAULT_SORT_KEY = 3
DEFAULT_ROWCOUNT = 9999

# sort_key -> (sort key, newest first?)
SORT_KEYS: dict[int, tuple[Callable[[ChestItem], Any], bool]] = {
    1: (itemgetter("date"), True),                          # acquisition date ("%Y-%m-%d")
    2: (itemgetter("bunrui_no", "b_hozon_sentou"), False),  # item category
    3: (lambda item: item["pokeitem"] or "", False),        # name
}


@endpoint("pdw.item.item_list")
def item_list(query: Query) -> dict:
    """Return the player's items, filtered, sorted, and paginated.

    Params:
        item_kind_id: 0 all items (default), 1 only Berries.
        sort_key: 1 newest first, 2 by category, 3 by name (default).
        offset: items to skip (default 0).
        rowcount: maximum items to return (default 9999).
        status: 2 returns the items queued for the Entralink instead.

    'cnt' in the response is the number of items before filtering.
    """
    if query_int(query, "status", 0) == ENTRALINK_QUEUE_STATUS:
        queued = save_data.read_game_sync().get("items", [])
        listed = [{**item, "pokeitem": text.lookup_str("item", item["pokeitem_id"])} for item in queued]
        return {"cnt": len(listed), "list": listed}

    chest = managers.get_chest().data["list"]
    items = chest
    if query_int(query, "item_kind_id", ItemKind.ALL) == ItemKind.BERRIES:
        items = [item for item in chest if is_berry(item["pokeitem_id"])]

    sort_key = SORT_KEYS.get(query_int(query, "sort_key", DEFAULT_SORT_KEY))
    if sort_key:
        key, newest_first = sort_key
        items = sorted(items, key=key, reverse=newest_first)

    offset = query_int(query, "offset", 0)
    rowcount = query_int(query, "rowcount", DEFAULT_ROWCOUNT)
    return {"cnt": len(chest), "list": items[offset:offset + rowcount]}


def parse_delivery_queue(query: Query) -> dict[int, int]:
    """Parse item_id[N]=<item id>_<count> params into {item id: count}.

    An empty queue is sent as a single empty item_id[] param.
    """
    queue = {}
    for key, value in query.items():
        if key.startswith("item_id") and value:
            item_id, count = value.split("_")
            queue[int(item_id)] = int(count)
    return queue


@endpoint("pdw.item.item_delivery_update", methods=("POST",))
def item_delivery_update(query: Query) -> dict:
    """Set the items to send to the Entralink.

    Items move between the Treasure Chest and the queue by the difference from the
    previous queue, so re-sending the same queue changes nothing.
    """
    logger.debug("item_delivery_update %s", query)

    requested = parse_delivery_queue(query)
    old_queue = {item["pokeitem_id"]: item["item_cnt"] for item in save_data.read_game_sync().get("items", [])}
    item_ids = requested.keys() | old_queue.keys()

    # what the queue gains, the chest loses, and only what the chest actually has is queued
    to_chest = {item_id: old_queue.get(item_id, 0) - requested.get(item_id, 0) for item_id in item_ids}
    moved = managers.get_chest().move_items(to_chest)
    queue = {item_id: old_queue.get(item_id, 0) - moved.get(item_id, 0) for item_id in item_ids}

    save_data.write_entralink_items([
        EntralinkItem(pokeitem_id=item_id, item_cnt=count) for item_id, count in queue.items() if count > 0
    ])
    return {}


@endpoint("pdw.item.item_trade_list", methods=("POST",))
def item_trade_list(_query: Query) -> list[ShareSlot]:
    """Return the player's Share Shelf."""
    return managers.get_shelf().data["share_list"]


@endpoint("pdw.item.friend_trade_list")
def friend_trade_list(query: Query) -> list[ShareSlot]:
    """Return another player's Share Shelf."""
    return managers.get_shelf(visits.find_player(int(query["other_member_savedata_id"]))).data["share_list"]


@endpoint("pdw.item.item_exhibit_update")
def item_exhibit_update(query: Query) -> list[ShareSlot]:
    """Move one of an item from the Treasure Chest to an empty slot of the Share Shelf."""
    item_id = int(query["item_id"])
    shelf = managers.get_shelf()
    material_id = shelf.place(int(query["x"]), int(query["y"]), item_id, save_data.require_gscd())
    try:
        managers.get_chest().remove_item(item_id, 1)
    except ValueError:
        shelf.take_back(material_id)
        raise
    return shelf.data["share_list"]


@endpoint("pdw.item.item_return_update")
def item_return_update(query: Query) -> list[ShareSlot]:
    """Move an item from the Share Shelf back to the Treasure Chest."""
    shelf = managers.get_shelf()
    managers.get_chest().add_item(shelf.take_back(int(query["material_id"])), 1)
    return shelf.data["share_list"]


@endpoint("pdw.item.item_trade_update")
def item_trade_update(query: Query) -> list[ShareSlot]:
    """Swap one of an item from the Treasure Chest for an item on a Share Shelf.

    The shelf can be the player's own or another player's.
    """
    item_id = int(query["item_id"])
    shelf = managers.get_shelf(visits.find_player(int(query["other_member_id"])))
    chest = managers.get_chest()
    chest.remove_item(item_id, 1)
    try:
        old_item_id = shelf.swap(int(query["other_material_id"]), item_id, save_data.require_gscd())
    except ValueError:
        chest.add_item(item_id, 1)
        raise
    chest.add_item(old_item_id, 1)
    return shelf.data["share_list"]
