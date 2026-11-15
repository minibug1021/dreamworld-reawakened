"""Structure of the stored data, and a glossary of the names the original API uses.

Everything except Account is JSON stored per Game Sync ID in game_sync_server's
player_saves table. These are TypedDicts so the data stays plain JSON-compatible dicts
while a type checker catches misspelled keys. The ones declared total=False describe data
whose fields may be absent (a fresh account, an empty garden plot, ...).
"""
from typing import Literal, NotRequired, TypedDict


class OwnedDecor(TypedDict):
    """One piece of decor the player owns.

    my_interior_id is unique across all players (db.next_id). interior_id says which
    catalog item it is. x and y are its position in the room, and are missing while it
    isn't placed.
    """

    my_interior_id: int
    interior_id: int
    x: NotRequired[int]
    y: NotRequired[int]


class Member(TypedDict, total=False):
    """The player_data["member"] column.

    It is written by the game-sync server at tuck-in (game_sync_server/.../player.py) and
    by this server.
    """

    member_id: int
    member_savedata_id: int | None
    gscd: str | None
    gsid: int | None
    gsid_count: int
    world_id: int
    pgl_name: str | None
    player_name: str | None
    trainer_gender: int | None  # 0 male, 1 female
    country_id: int | None
    langcode: int | None
    rom_id: int | None
    rom_name: str | None  # only filled in responses (pgl.top.init)
    alter_rom_name: str | None
    player_badge_num: int | None
    avator_id: int
    avator_name: str | None
    disclosure_flag: int
    list_disclosure_flag: int
    disable_flag: int
    special_flag: int
    special_disp_flag: int
    bridge_flag: int
    trial_flag: int
    first_flag: int
    is_initializing: int
    is_downloaded: int
    member_created_at: str
    # the tucked-in Pokémon
    pokemon_no: int | None
    form_no: int | None
    pokemon_name: str | int | None
    type1: int | None
    type2: int | None
    sleeping_flag: int
    isin_sleep_pokemon: int
    sleep_time: int
    sleep_pokemon_count: int
    send_pokemon_count: int
    play_status: int  # utils.constants.PlayerStatus
    # Dream Points
    point: int
    experiment_point: int
    # house
    island_id: int
    shelf_id: int
    wateringpot_id: int  # the selected Watering Can's interior_id
    my_interior_list: list[OwnedDecor]  # the room's arranged_interior_list is built from this
    # timestamps
    last_started_at: int | None
    last_logined_at: int | None
    last_started_at_timezone: int | None
    last_up_time: str | None
    last_up_time_strict: str | None
    pdw_copied_at: str | None
    pgl_copied_at: str | None
    deleted_at: str | None
    nextstart_remaintime: int
    # Berries converted to Dream Points after a long absence
    item_deleted_flag: int
    item_deleted_point: int
    # E-Z Mail
    unread_mail_count: int


class PlayerData(TypedDict, total=False):
    """The player_data column."""

    member: Member
    token: str | None
    medals: list[int]  # the obtained Medal ids, newest first (Black 2 / White 2 only)
    favorite_medal: int | None  # the Medal the player chose to show off


class SleepingPokemon(TypedDict, total=False):
    """The tucked-in Pokémon (game_sync_server's PkmnInfo)."""

    pokemon_no: int
    form_no: int
    type1: int
    type2: int
    pokemon_nickname: str
    oyaname: str
    level: int
    sex: int
    personality: int  # the nature id (0-24)
    ball_name: int
    is_shiny: bool


class EntralinkItem(TypedDict):
    """An item queued to go to the DS through the Entralink."""

    pokeitem_id: int
    item_cnt: int


class GameSync(TypedDict, total=False):
    """What the DS gets at the next Game Sync (written by both servers)."""

    levels_gained: int
    country: int | None  # country and region IDs
    region: int | None
    hours_played: int
    minutes_played: int
    cgear_skin: str | None
    dex_skin: str | None
    musical: str | None
    encounters: list[dict]
    items: list[EntralinkItem]
    avenue_visitors: list[dict]
    loblolly_decor: int | None  # the id of the Loblolly item picked on the DS


class ChestItem(TypedDict, total=False):
    """One stack of items in the Treasure Chest."""

    pokeitem_id: int
    item_cnt: int
    date: str  # "%Y-%m-%d"
    # added on load by ChestManager, not saved
    pokeitem: str | None
    bunrui_no: int
    b_hozon_sentou: int
    field_line1: str | None
    field_line2: str | None
    field_line3: str | None


class ChestData(TypedDict):
    """The chest_data column.

    cnt is len(list).
    """

    cnt: int
    list: list[ChestItem]


class GrowthState(TypedDict):
    """Server-side growth state of a planted Berry.

    The times are epochs.
    """

    planted_at: int
    updated_at: int  # growth has been worked out up to here
    watered_at: int
    berry_hp: int    # lost while the soil is dry


class Plot(TypedDict, total=False):
    """One garden plot."""

    my_croft_id: int
    x: int
    y: int
    # only while something is planted
    pokeitem_id: int
    dirt_hp: int
    kinomi_state: int
    server: GrowthState
    # added on load by CropManager, not saved
    kinomi: str | None
    kinomi_id: int
    desc1: str | None
    desc2: str | None
    desc3: str | None


class CropData(TypedDict, total=False):
    """The crop_data column."""

    croft_list: list[Plot]
    diglett_flag: int


# who can see a Trainer Club account's PGL or Dream World profile
Privacy = Literal["everyone", "friends", "nobody"]


class Account(TypedDict):
    """A row of the accounts table (utils.account_manager). Each row is one Trainer Club login."""

    username: str
    password_hash: str
    email: str
    country: int | None  # a raw_text/<lang>/country.txt id
    birth_month: int | None  # 1 to 12
    pgl_privacy: Privacy | None
    dw_privacy: Privacy | None
    activated: int
    activation_token: str | None
    active_gscd: str | None
    last_daily_bonus_date: str | None  # JST "%Y-%m-%d"
    shows_shiny: int
