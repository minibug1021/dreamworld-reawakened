"""pdw.interior.*: the Dream Catalogue and room layout (pdw_catalog.swf, pdw_room.swf).

The swf sends some of these as GET and some as POST, so every endpoint accepts both.
"""
from api.routes import GET_AND_POST, Query, endpoint, query_int
from utils import save_data
from utils.decor import (
    CATALOG,
    MASTER_IDS,
    DecorCategory,
    arrange_decor,
    catalog_entry,
    catalog_name,
    charge_for_decor,
    find_owned,
    get_decor,
    grant_decor,
    owned_decor,
)

DEFAULT_CATALOG_ID = 1


@endpoint("pdw.interior.interior_catalog_list", methods=GET_AND_POST)
def interior_catalog_list(_query: Query) -> list[dict]:
    """Every catalog that sells something."""
    catalog_ids = sorted({decor.catalog_id for decor in CATALOG.values() if decor.catalog_id is not None})
    return [
        {"interior_catalog_id": str(catalog_id), "interior_catalog_name": catalog_name(catalog_id)}
        for catalog_id in catalog_ids
    ]


@endpoint("pdw.interior.interior_list", methods=GET_AND_POST)
def interior_list(query: Query) -> list[dict]:
    """Every item in the requested catalog (param: interior_catalog_id, default 1)."""
    catalog_id = int(query.get("interior_catalog_id") or DEFAULT_CATALOG_ID)

    my_ids: dict[int, int] = {}  # interior_id -> the first copy the player owns
    for owned in owned_decor():
        my_ids.setdefault(owned["interior_id"], owned["my_interior_id"])

    return [
        catalog_entry(decor, my_ids.get(decor.id)) for decor in CATALOG.values()
        if decor.catalog_id == catalog_id and decor.id not in MASTER_IDS
    ]


@endpoint("pdw.interior.interior_layout_update", methods=GET_AND_POST)
def interior_layout_update(query: Query) -> dict:
    """Replace the whole room layout.

    The body has interior[N] = "<my_interior_id>_<x>_<y>_<arranged 1|0>" for each owned
    item. Anything not sent as arranged is taken out of the room.
    """
    placed: dict[int, tuple[int, int]] = {}
    for key, value in query.items():
        if not key.startswith("interior["):
            continue
        my_id, x, y, arranged = (int(part) for part in value.split("_"))
        if arranged == 1:
            placed[my_id] = (x, y)

    arrange_decor(placed)
    return {}


@endpoint("pdw.interior.my_interior_insert", methods=GET_AND_POST)
def my_interior_insert(query: Query) -> list[dict]:
    """Charge the player for a decor item and give it to them."""
    decor_id = query_int(query, "interior_id", 0)
    if decor_id not in CATALOG:
        raise ValueError(f"No decor {decor_id}")
    charge_for_decor(decor_id)
    return [{"my_interior_id": grant_decor(decor_id)}]


@endpoint("pdw.interior.interior_change_update", methods=GET_AND_POST)
def interior_change_update(query: Query) -> dict:
    """Switches to an owned house or shelf."""
    decor_id = find_owned(query_int(query, "my_interior_id", 0))["interior_id"]
    category = get_decor(decor_id).category_id
    if category == DecorCategory.HOUSE:
        save_data.update_member({"island_id": decor_id})
    elif category == DecorCategory.SHELF:
        save_data.update_member({"shelf_id": decor_id})
    return {}
