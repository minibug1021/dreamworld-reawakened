"""pdw.croft.*: the Berry garden (pdw_farm.swf)."""
from api.routes import GET_AND_POST, Query, endpoint
from game_sync_server.entralinked.utility.db_manager import db
from utils import managers, save_data, visits
from utils.constants import WATERINGCAN_ID
from utils.decor import get_decor, owned_wateringcans
from utils.models import CropData


@endpoint("pdw.croft.my_croft_list")
def my_croft_list(_query: Query) -> CropData:
    """Return the player's Berry garden, after growing the Berries and checking for an expansion."""
    crops = managers.get_crops()
    crops.process_berry_growth()
    crops.check_garden_expansion()
    return crops.data


@endpoint("pdw.croft.waterpot_list", methods=GET_AND_POST)
def wateringcan_list(_query: Query) -> dict:
    """Return the player's Watering Cans and which one is in use.

    IDs technically range from 1-6, but 2-6 were never implemented.
    """
    selected_id = save_data.read_member().get("wateringpot_id", WATERINGCAN_ID)
    wateringcans = owned_wateringcans()
    selected = next((can for can in wateringcans if can["interior_id"] == selected_id), wateringcans[0])
    return {
        "waterpot_list": [
            {
                "my_interior_id": can["my_interior_id"],
                "interior_id":    can["interior_id"],
                "selected_flag":  int(can is selected),
                "interior_name":  get_decor(can["interior_id"]).name,
            }
            for can in wateringcans
        ]
    }


@endpoint("pdw.croft.kinomi_harvesting", methods=("POST",))
def harvest(query: Query) -> dict:
    """Put a plot's Berries into the Treasure Chest."""
    harvest_result = managers.get_crops().harvest(int(query["my_croft_id"]))
    managers.get_chest().add_item(harvest_result["pokeitem_id"], harvest_result["count"])
    return harvest_result


@endpoint("pdw.croft.kinomi_sowing", methods=("POST",))
def sow(query: Query) -> CropData:
    """Plants one Berry from the Treasure Chest."""
    pokeitem_id = int(query["pokeitem_id"])
    managers.get_chest().remove_item(pokeitem_id, 1)
    crops = managers.get_crops()
    crops.sow(int(query["my_croft_id"]), pokeitem_id)
    return crops.data


@endpoint("pdw.croft.kinomi_watering", methods=("POST",))
def water(query: Query) -> CropData:
    """Waters a plot."""
    crops = managers.get_crops()
    crops.water_plot(int(query["my_croft_id"]))
    return crops.data


@endpoint("pdw.croft.friend_croft_list")
def friend_croft_list(query: Query) -> dict:
    """Return another player's Berry garden, and how many times the player can still water it today."""
    crops = managers.get_crops(visits.find_player(int(query["member_savedata_id"])))
    crops.process_berry_growth()
    return {**crops.data, "remains_watering": visits.friend_waterings_left()}


@endpoint("pdw.croft.friend_kinomi_watering", methods=("POST",))
def friend_water(query: Query) -> dict:
    """Waters a plot in another player's garden, using up one of today's waterings."""
    if visits.friend_waterings_left() <= 0:
        raise ValueError("No waterings left today")
    friend = visits.find_player(int(query["member_savedata_id"]))
    crops = managers.get_crops(friend)
    crops.water_plot(int(query["my_croft_id"]))
    left = visits.use_friend_watering()
    db.mark_footprint(friend, save_data.require_gscd(), "watered", save_data.now_jst_str())
    return {**crops.data, "remains_watering": left}
