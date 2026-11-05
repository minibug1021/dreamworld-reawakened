"""pdw.croft.*: the Berry garden (pdw_farm.swf)."""
from api.routes import GET_AND_POST, Query, endpoint
from utils import managers, save_data
from utils.decor import WATERINGCAN_ID, get_decor, owned_wateringcans
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
