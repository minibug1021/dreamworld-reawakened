"""Game ids and enums shared across the server."""
from enum import IntEnum

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR


class Rom(IntEnum):
    """member.rom_id: which cartridge the Game Sync ID belongs to (raw_text/*/game.txt order)."""

    WHITE = 20
    BLACK = 21
    WHITE_2 = 22
    BLACK_2 = 23


def is_b2w2(rom_id: int | None) -> bool:
    """Whether a rom_id is Black 2 or White 2 (rather than Black or White)."""
    return rom_id in (Rom.WHITE_2, Rom.BLACK_2)


class PlayerStatus(IntEnum):
    """Values of member.play_status."""

    AWAKE = 0
    PLAY_READY = 1
    DREAMING = 2
    WAKE_READY = 3


NATURE_COUNT = 25  # nature ids 0-24 (raw_text/*/nature.txt)
