"""The Dream Catalogue (json_data/catalog.json) and the decor a player owns.

Decor is anything the catalog sells: furniture, houses, shelves, and Watering Cans. The
game's API calls it "interior". A player's copies live in member["my_interior_list"]
(models.OwnedDecor).
"""
from dataclasses import dataclass
from enum import IntEnum
from itertools import zip_longest

from game_sync_server.entralinked.utility.db_manager import db
from utils import managers, save_data, text
from utils.berries import to_item_id
from utils.data import load_json_data
from utils.models import Member, OwnedDecor


class DecorCategory(IntEnum):
    """interior_category_id values the code cares about."""

    HOUSE = 1
    WATERINGCAN = 2
    SHELF = 3
    MISC = 26


class PlaceType(IntEnum):
    """place_type: where in the room a piece of decor can go."""

    ANYWHERE = 0
    WALL = 1
    FLOOR = 2
    MAT = 3


WATERINGCAN_ID = 1

# Houses and shelves. 302 is unused.
HOUSE_ISLAND_IDS = (201, 202, 203, 1082, 1099, 1106, 1113, 1114, 1176, 1206, 1268)
HOUSE_SHELF_IDS  = (301, 302)

# The swf adds the treasure chest (9990001) and friend board (9990003) to the default
# catalog itself, and the Dream Catalogue (9990002) isn't something you buy.
MASTER_IDS = frozenset({9990001, 9990002, 9990003})

COST_SLOTS = ("", "2", "3")  # kinomi_id/kinomi/price, kinomi_id2/..., kinomi_id3/...


@dataclass(frozen=True)
class Decor:
    """One catalog item."""

    id: int
    category_id: int
    catalog_id: int | None = None           # None if it isn't sold in any catalog
    cost: tuple[tuple[int, int], ...] = ()  # (berry_id, count) per slot
    size_w: int | None = None
    size_h: int | None = None
    place_type: int | None = None
    arrangement_flag: int | None = None
    movable_flag: int | None = None
    is_ds: int = 0

    @property
    def size(self) -> tuple[int, int]:
        """The decor's (width, height). (0, 0) if either is unknown."""
        if self.size_w is not None and self.size_h is not None:
            return self.size_w, self.size_h
        return 0, 0

    @property
    def category_name(self) -> str | None:
        """The display name of the decor's category. None if it has none."""
        return text.lookup_str("decor_category", self.category_id)

    @property
    def name(self) -> str:
        """The decor's display name, or its category name and id if it has none."""
        return text.lookup_str("decor", self.id) or f"{self.category_name} #{self.id}"

    def common_fields(self) -> dict:
        """Fields both interior_list and arranged_interior_list entries carry."""
        size_w, size_h = self.size
        return {
            "interior_id":          self.id,
            "interior_name":        self.name,
            "interior_size_w":      size_w,
            "interior_size_h":      size_h,
            "interior_category_id": self.category_id,
            "place_type":           PlaceType.ANYWHERE if self.place_type is None else self.place_type,
        }

    def cost_fields(self) -> dict:
        """kinomi_id/kinomi/price for up to 3 berries. An empty slot has a null kinomi_id."""
        fields: dict = {}
        for suffix, cost in zip_longest(COST_SLOTS, self.cost[:len(COST_SLOTS)]):
            if cost is None:
                fields.update({f"kinomi_id{suffix}": None, f"kinomi{suffix}": "", f"price{suffix}": 0})
                continue
            berry_id, count = cost
            item_id = to_item_id(berry_id)
            fields.update({f"kinomi_id{suffix}": item_id,
                           f"kinomi{suffix}": text.lookup_str("item", item_id),
                           f"price{suffix}": count})
        return fields


def _load_catalog() -> dict[int, Decor]:
    return {
        int(decor_id): Decor(
            id=int(decor_id),
            catalog_id=entry["catalog_id"],
            category_id=entry["catalog_type"],
            cost=tuple((cost["berry_id"], cost["count"]) for cost in entry["cost"]),
            size_w=entry["size_w"], size_h=entry["size_h"], place_type=entry["place_type"],
            arrangement_flag=entry["arrangement_flag"], movable_flag=entry["movable_flag"],
            is_ds=entry["is_ds"] or 0,
        )
        for decor_id, entry in load_json_data("catalog").items()
    }


CATALOG = _load_catalog()


def catalog_name(catalog_id: int) -> str:
    """Return a catalog's display name."""
    return text.lookup_str("catalog", catalog_id) or f"Catalogue {catalog_id}"


def get_decor(decor_id: int) -> Decor:
    """Return the catalog data for an id.

    Ids not sold by any catalog (some houses) get just a category.
    """
    if decor_id in CATALOG:
        return CATALOG[decor_id]
    if decor_id in HOUSE_ISLAND_IDS:
        return Decor(decor_id, DecorCategory.HOUSE)
    if decor_id in HOUSE_SHELF_IDS:
        return Decor(decor_id, DecorCategory.SHELF)
    return Decor(decor_id, DecorCategory.MISC)


def owned_decor(gscd: str | None = None) -> list[OwnedDecor]:
    """All the decor the player owns, placed in the room or not."""
    return save_data.read_member(gscd).get("my_interior_list") or []


def find_owned(my_decor_id: int, gscd: str | None = None) -> OwnedDecor:
    """Return the player's copy with this id. Raise ValueError if they don't own it."""
    owned = next((o for o in owned_decor(gscd) if o["my_interior_id"] == my_decor_id), None)
    if owned is None:
        raise ValueError(f"No owned decor {my_decor_id}")
    return owned


def charge_for_decor(decor_id: int, gscd: str | None = None) -> None:
    """Deduct the cost of a decor item from the player's chest.

    Raise ValueError, and deduct nothing, if they can't afford it.
    """
    decor = get_decor(decor_id)
    cost = tuple((to_item_id(berry_id), count) for berry_id, count in decor.cost)
    managers.get_chest(gscd).remove_items(cost)


def grant_decor(decor_id: int, gscd: str | None = None) -> int:
    """Give the player a new copy of `decor_id`.

    Return its new (globally unique) my_interior_id.
    """
    gscd = save_data.require_gscd(gscd)
    [my_decor_id] = db.next_id("my_interior_id")
    owned: OwnedDecor = {"my_interior_id": my_decor_id, "interior_id": decor_id}

    def add(member: Member) -> None:
        member.setdefault("my_interior_list", []).append(owned)

    save_data.change_member(add, gscd)
    return my_decor_id


def owned_wateringcans() -> list[OwnedDecor]:
    """Return the player's Watering Cans.

    A player who has none is given the basic one first.
    """
    wateringcans = [owned for owned in owned_decor()
                    if get_decor(owned["interior_id"]).category_id == DecorCategory.WATERINGCAN]
    if not wateringcans:
        grant_decor(WATERINGCAN_ID)
        wateringcans = [owned for owned in owned_decor() if owned["interior_id"] == WATERINGCAN_ID]
    return wateringcans


def catalog_entry(decor: Decor, my_decor_id: int | None) -> dict:
    """Return an interior_list entry as pdw_catalog.swf reads it.

    my_decor_id is the player's copy of it, if they own one.
    """
    return {
        **decor.common_fields(),
        "interior_desc":          "",
        "interior_category_name": decor.category_name,
        "arrangement_flag":       decor.arrangement_flag,
        "movable_flag":           decor.movable_flag,
        "is_ds":                  decor.is_ds,
        "new_flag":               0,
        "limited_flag":           0,
        "my_interior_id":         my_decor_id,
        **decor.cost_fields(),
    }


def arranged_entry(owned: OwnedDecor) -> dict:
    """Return an arranged_interior_list entry as pdw_room.swf reads it, for a placed piece of decor.

    Only the id and position are stored. Everything else comes from the catalog. The
    game never sends a rotation (note its own 'roatation' spelling).
    """
    decor = get_decor(owned["interior_id"])
    return {
        "my_interior_id":   owned["my_interior_id"],
        **decor.common_fields(),
        "special_flag":     0,
        "movable_flag":     1 if decor.movable_flag is None else decor.movable_flag,
        "arrangement_flag": 1 if decor.arrangement_flag is None else decor.arrangement_flag,
        "x":                owned["x"],
        "y":                owned["y"],
        "roatation":        0,
    }


def arranged_decor(gscd: str | None = None) -> list[dict]:
    """Return the room's arranged_interior_list, which holds every piece of owned decor that has a position."""
    return [arranged_entry(owned) for owned in owned_decor(gscd) if "x" in owned]
