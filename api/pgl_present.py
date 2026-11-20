"""pgl.present.*: the Customize page (present.swf) for picking C-Gear skins, Pokédex skins, and Musicals."""
from functools import cache
from pathlib import Path, PurePosixPath
from typing import Literal

from api.routes import Query, endpoint
from config import ROOT_DIR
from utils import save_data
from utils.constants import is_b2w2
from utils.data import load_json_data
from utils.language import current_language
from utils.models import GameSync, Member

_PRESENTS: dict[str, dict] = load_json_data("customize")

_SkinField = Literal["cgear_skin", "dex_skin", "musical"]

# category -> GameSync field. present_list calls the category's list <category>_list,
# and present_dldata_update takes its pick as <category>_id.
_CATEGORIES: dict[str, _SkinField] = {
    "cgear":   "cgear_skin",
    "zukan":   "dex_skin",
    "musical": "musical",
}


def _img_dir(lang: str) -> Path:
    """Return the folder with the language's present thumbnails and Musical mp3s."""
    return (ROOT_DIR / "dreamworld_assets" / f"{lang}.pokemon-gl.com"
            / "src" / "swf" / "customize" / "assets" / lang / "img")


def _musical_file(entry: dict, lang: str) -> str | None:
    """Return the URL of the Musical's mp3, which sits next to its thumbnail."""
    thumb = entry["data"][lang][2]
    if entry["type"] != "MUSICAL" or not thumb:
        return None
    img_dir = _img_dir(lang)
    mp3 = min((img_dir / thumb).parent.glob("*.mp3"), default=None)
    return "/" + mp3.relative_to(img_dir).as_posix() if mp3 else None


@cache
def _musical_files(lang: str) -> dict[str, str | None]:
    """Present id -> the URL of the Musical's mp3 in that language (None for other presents)."""
    return {present_id: _musical_file(entry, lang) for present_id, entry in _PRESENTS.items()}


def _dlc_filenames(entry: dict) -> list[str]:
    """Return the file names in every language."""
    return [PurePosixPath(file).name for _, file, _ in entry["data"].values() if file]


def _dlc_filename(entry: dict) -> str | None:
    """Return the file name in the visitor's language.

    Return None otherwise.
    """
    file = entry["data"][current_language()][1]
    return PurePosixPath(file).name if file else None


def _folder(category: str, member: Member) -> str:
    """Return the customize.json type that holds the category's skins for the player's game."""
    if category == "cgear":
        return "CGEAR2" if is_b2w2(member.get("rom_id")) else "CGEAR"
    return category.upper()


def _offered(entry: dict, category: str, member: Member) -> bool:
    """Return whether a DLC is valid for the player's game."""
    trainer_gender = "female" if member.get("trainer_gender") == 1 else "male"
    return entry["type"] == _folder(category, member) and entry.get("gender", trainer_gender) == trainer_gender


def _name(entry: dict) -> str:
    """Return the DLC's name in the visitor's language, else in English."""
    return entry["data"][current_language()][0] or entry["data"]["en"][0]


def _entry(present_id: str, entry: dict) -> dict | None:
    """Build the DLC's present_list item.

    Return None if the visitor's language lacks its file or thumbnail."""
    thumb = entry["data"][current_language()][2]
    if thumb is None or _dlc_filename(entry) is None:
        return None
    item = {
        "present_id":   present_id,
        "present_file": "/" + thumb,
        "present_name": _name(entry),
        "is_select":    "0",
    }
    if musical_file := _musical_files(current_language())[present_id]:
        item["musical_file"] = musical_file
    return item


@endpoint("pgl.present.present_list")
def present_list(_query: Query) -> dict:
    """Return the C-Gear skins, Pokédex skins, and Musicals the player can pick."""
    game_sync = save_data.read_game_sync()
    member = save_data.read_member()
    response = {}
    # basic/default skins first, then the rest in customize.json order
    presents = sorted(_PRESENTS.items(), key=lambda item: not item[1].get("default"))
    for category, field in _CATEGORIES.items():
        selected = game_sync.get(field)
        items = []
        for present_id, entry in presents:
            item = _entry(present_id, entry) if _offered(entry, category, member) else None
            if item is None:
                continue

            if selected in _dlc_filenames(entry):
                item["is_select"] = "1"
                selected = None
            items.append(item)
        response[f"{category}_list"] = items
    return response


@endpoint("pgl.present.present_dldata_update", methods=("POST",))
def present_dldata_update(query: Query) -> dict:
    """Store the file names of the DLC the player picked, for Game Sync to send."""
    member = save_data.read_member()
    changes: GameSync = {}
    for category, field in _CATEGORIES.items():
        entry = _PRESENTS.get(query.get(f"{category}_id") or "")
        if entry is None or not _offered(entry, category, member):
            continue
        dlc = _dlc_filename(entry)
        if dlc:
            changes[field] = dlc
    if changes:
        save_data.change_game_sync(lambda game_sync: game_sync.update(changes))
    return {}
