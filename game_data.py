#!/usr/bin/env python3
import json
import time
from pathlib import Path
from random import choice
from random import randint
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent

# --------------------
# Helper data
# --------------------

with open(ROOT_DIR / "json_data" / "items.json", encoding="UTF-8") as f:
    item_info = json.load(f)

with open(ROOT_DIR / "json_data" / "pokemon.json", encoding="UTF-8") as f:
    pokemon_info = json.load(f)

with open(ROOT_DIR / "json_data" / "dream_islands.json", encoding="UTF-8") as f:
    area_info = json.load(f)

with open(ROOT_DIR / "json_data" / "berries.json", encoding="UTF-8") as f:
    berry_data = json.load(f)

pokemon_natures = ("Adamant","Bashful","Bold","Brave","Calm","Careful","Docile","Gentle","Hardy","Hasty","Impish","Jolly","Lax","Lonely","Mild","Modest","Naive","Naughty","Quiet","Quirky","Rash","Relaxed","Sassy","Serious","Timid")

# --------------------
# Helper functions
# --------------------

def generate_otoken():
    return f"{randint(1, 99)}dwt{player_data['member']['world_id']}{format(int(time.time()), 'x')}.{randint(10000000, 99999999)}"

def date_to_unix(datetime_string: str):
    return datetime.strptime(datetime_string, "%Y-%m-%d")

def get_random_pokemon(restriction_list: list[int] = []) -> dict[str: str|None]:
    if restriction_list == []:
        pkmn_options = [i for i in list(pokemon_info.keys())]
    else:
        pkmn_options = [i for i in list(pokemon_info.keys()) if int(i.split("-")[0]) in restriction_list]

    pkmn = choice(pkmn_options)
    natdex = pkmn.split("-")[0]

    return {**pokemon_info[pkmn], "pokemon_no": natdex}

# --------------------
# Save data manager classes
# --------------------

class ChestManager:
    def __init__(self, data_path):
        self.path = data_path
        with open(self.path, encoding="UTF-8") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.path, "w", encoding="UTF-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def fetch_item_by_id(self, item_id):
        return next((item for item in self.data["list"] if item["pokeitem_id"] == item_id), None)

    def add_item(self, item_id, count):
        current_date = datetime.now().strftime("%Y-%m-%d")

        chest_item = self.fetch_item_by_id(item_id)

        if chest_item:
            chest_item["item_cnt"] += count
            chest_item["date"] = current_date

        else:
            curr_item_info = item_info[str(item_id)]
            self.data["cnt"] += 1
            new_item = {
                "pokeitem_id": item_id,
                "pokeitem": curr_item_info["item_name"],
                "item_cnt": 1,
                "bunrui_no": "1",
                "b_hozon_sentou": "1",
                "date": current_date,
                "field_line1": curr_item_info["desc"][0],
                "field_line2": curr_item_info["desc"][1],
                "field_line3": curr_item_info["desc"][2]
            }
            self.data["list"].append(new_item)

        self.save()

    def remove_item(self, item_id, count):
        current_date = datetime.now().strftime("%Y-%m-%d")
        chest_item = self.fetch_item_by_id(int(item_id))

        chest_item["item_cnt"] -= count
        chest_item["date"] = current_date

        if chest_item["item_cnt"] <= 0:
            item_index = self.data["list"].index(chest_item)
            del self.data["list"][item_index]
            self.data["cnt"] -= 1

        self.save()


class CropManager:
    def __init__(self, data_path):
        self.path = data_path
        with open(self.path, encoding="UTF-8") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.path, "w", encoding="UTF-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def fetch_plot_by_id(self, my_croft_id):
        return next((p for p in self.data["croft_list"] if p["my_croft_id"] == my_croft_id), None)
    
    def water_plot(self, my_croft_id):
        plot = self.fetch_plot_by_id(my_croft_id)
        plot["dirt_hp"] = 100

        self.save()

    def sow(self, my_croft_id, pokeitem_id):
        plot = self.fetch_plot_by_id(my_croft_id)

        current_time = round(time.time())

        berry_id = int(pokeitem_id) - 148

        plot.update({
            "my_croft_id": my_croft_id,
            "pokeitem_id": int(pokeitem_id),
            "kinomi": item_info[pokeitem_id]["item_name"],
            "kinomi_id": berry_id,
            "dirt_hp": 100,
            "desc1": item_info[pokeitem_id]["desc"][0],
            "desc2": item_info[pokeitem_id]["desc"][1],
            "desc3": item_info[pokeitem_id]["desc"][2],
            "kinomi_state": 0,
            "x": plot["x"],
            "y": plot["y"],
            "server": {"planted_time": current_time, "last_update_time": current_time, "yield": berry_data[str(berry_id)]["max_yield"]}
        })

        self.save()

    def harvest(self, my_croft_id):
        plot = self.fetch_plot_by_id(my_croft_id)
        plot_index = self.data["croft_list"].index(plot)
        
        harvest_data = {
            "kinomi_id": plot["kinomi_id"],
            "kinomi": plot["kinomi"],
            "pokeitem_id": plot["pokeitem_id"],
            "count": plot["server"]["yield"]
        }
        
        self.data["croft_list"][plot_index] = {"my_croft_id": my_croft_id, "x": plot["x"], "y": plot["y"]}
        
        self.save()

        return harvest_data
    
    def process_berry_growth(self):
        current_time = round(time.time())

        for plant in self.data["croft_list"]:
            if "dirt_hp" not in plant:
                continue

            curr_berry_data = berry_data[str(plant["kinomi_id"])]

            hours_since_planted = (current_time - plant["server"]["planted_time"]) // 3600
            hours_since_update = (current_time - plant["server"]["last_update_time"]) // 3600

            hours_at_last_update = hours_since_planted - hours_since_update

            single_stage_time = curr_berry_data["grow_time"] / 4

            for hour in range(1, hours_since_update + 1):
                total_hours = hours_at_last_update + hour
                plant["kinomi_state"] = min(total_hours // single_stage_time, 4)

                if (plant["dirt_hp"] == 0) and (plant["kinomi_state"] != 4): #remove 1/5th of the berry's max, but no lower than 2 berries
                    #I am also assuming that plants which are ready to harvest will not lose berry yield
                    plant["server"]["yield"] = max(plant["server"]["yield"] - (curr_berry_data["max_yield"] * 0.2), 2)
                else:
                    plant["dirt_hp"] -= curr_berry_data["drain_rate"]
            
            if plant["dirt_hp"] < 0:
                plant["dirt_hp"] = 0

            plant["server"]["last_update_time"] = current_time

        self.save()
    
# --------------------
# Save data
# --------------------

with open(ROOT_DIR / "save_data" / "player_data.json", encoding="UTF-8") as f:
    player_data = json.load(f)

chest = ChestManager(ROOT_DIR / "save_data" / "chest_data.json")

crops = CropManager(ROOT_DIR / "save_data" / "crop_data.json")