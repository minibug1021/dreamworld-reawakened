"""pgl.journal.*: site-wide statistics."""
import time
from collections import Counter, defaultdict

from api.routes import Query, endpoint
from game_sync_server.entralinked.utility.db_manager import db
from utils import save_data, text
from utils.account_manager import accounts
from utils.messages import message


@endpoint("pgl.journal.census")
def census(_query: Query) -> dict:
    """Return the census data, which shows the "Most tucked-in Pokémon" leaderboard per country.

    It counts every gscd's currently tucked-in Pokémon (member.pokemon_no).
    """
    species_by_country: defaultdict[int, Counter[int]] = defaultdict(Counter)

    for gscd in db.get_all_gscds():
        member = save_data.read_member(gscd)
        pokemon_no = member.get("pokemon_no")

        if pokemon_no is None:
            continue

        country_id = accounts.get_country_id(accounts.get_gscd_owner(gscd))
        if country_id is None:
            continue

        species_by_country[country_id][pokemon_no] += 1

    country_ranking = sorted(
        species_by_country.items(), key=lambda item: sum(item[1].values()), reverse=True
    )

    lead = message("most_tucked_in")
    ranking_list = []
    country_list = []

    for rank, (country_id, species_counts) in enumerate(country_ranking, start=1):
        total = sum(species_counts.values())
        top_species = [pokemon_no for pokemon_no, _ in species_counts.most_common()]
        label = message("tuck_in_count", count=total)

        ranking_list.append({
            "ranking": rank,
            "country_id": country_id,
            "country_name": text.lookup_str("country", country_id),
            "pokemon_no": top_species[0],
            "label": label,
            "title": lead,
        })

        country_list.append({
            "country_id": country_id,
            "census_list": [{
                "lead": lead,
                "title": lead,
                "ranking": rank,
                "label": label,
            }],
            "pokemon_list": [{"pokemon_no": pokemon_no} for pokemon_no in top_species],
        })

    return {
        "census_list":  [{"lead": lead, "ranking_list": ranking_list}],
        "country_list": country_list,
        "updated_at":   int(time.time()),
    }
