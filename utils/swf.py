"""Parameters for embedding the Dream World SWF."""
import json

from utils import save_data
from utils.language import current_language


def build_swf_params() -> dict:
    """Return the parameters for embedding the Dream World SWF for the logged-in player."""
    player_data = save_data.read_player_data()
    return {
        "json": json.dumps({
            "member": player_data["member"],
            "token":  player_data.get("token", ""),
            "medals": save_data.read_medals(),
        }),
        "v":             "2.0",
        "api_host_name": "/api/",
        "page":          "SITE_PDW",
        "lang":          f"{current_language()}.",
    }
