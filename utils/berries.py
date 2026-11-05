"""Berry ids.

A Berry has a kinomi_id (1-64, Cheri first) and an item id like any other item
(149-212). The two differ by a fixed offset.
"""
BERRY_ITEM_ID_OFFSET = 148
BERRY_COUNT = 64

BERRY_ITEM_IDS = range(BERRY_ITEM_ID_OFFSET + 1, BERRY_ITEM_ID_OFFSET + BERRY_COUNT + 1)  # 149-212


def to_item_id(berry_id: int) -> int:
    """Item id of a kinomi_id."""
    return berry_id + BERRY_ITEM_ID_OFFSET


def to_berry_id(item_id: int) -> int:
    """kinomi_id of a Berry's item id."""
    return item_id - BERRY_ITEM_ID_OFFSET


def is_berry(item_id: int) -> bool:
    """Whether an item id is a Berry."""
    return item_id in BERRY_ITEM_IDS
