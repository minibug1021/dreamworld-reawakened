import json
import time
from pathlib import Path
from datetime import datetime

from utils import text
from utils import save_data
from game_sync_server.entralinked.utility.db_manager import db

ROOT_DIR = Path(__file__).resolve().parent.parent

with open(ROOT_DIR / "json_data" / "items.json", encoding="UTF-8") as f:
    item_info = json.load(f)

with open(ROOT_DIR / "json_data" / "berries.json", encoding="UTF-8") as f:
    berry_data = json.load(f)

class ChestManager:
    """Manages the player's Treasure Chest.

    Attributes:
        data: A dictionary containing the loaded chest inventory data.
    """

    def __init__(self):
        self._redundant_fields = {"pokeitem", "bunrui_no", "b_hozon_sentou", "field_line1", "field_line2", "field_line3"}
        self.data = db.read(save_data.gscd, "chest_data")

    def update_json(self):
        for item in self.data["list"]:
            pokeitem_id = item["pokeitem_id"]

            item_desc = text.lookup_str("item_descriptions", pokeitem_id)

            item["pokeitem"] = text.lookup_str("item", pokeitem_id)

            item_sort_data = item_info[str(pokeitem_id)]

            item["bunrui_no"] = item_sort_data["first_sort"]
            item["b_hozon_sentou"] = item_sort_data["second_sort"]

            item["field_line1"] = item_desc[0]
            item["field_line2"] = item_desc[1]
            item["field_line3"] = item_desc[2]

    def save(self):
        chest_data = {
            "cnt": len(self.data["list"]),
            "list": [
                {k: v for k, v in item.items() if k not in self._redundant_fields}
                for item in self.data["list"]
            ]
        }

        db.write(save_data.gscd, "chest_data", chest_data)

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

            item_desc = text.lookup_str("item_descriptions", item_id)
            new_item = {
                "pokeitem_id": item_id,
                "pokeitem": text.lookup_str("item", item_id),
                "item_cnt": count,
                "bunrui_no": curr_item_info["first_sort"],
                "b_hozon_sentou": curr_item_info["second_sort"],
                "date": current_date,
                "field_line1": item_desc[0],
                "field_line2": item_desc[1],
                "field_line3": item_desc[2]
            }
            self.data["list"].append(new_item)

        self.save()

    def remove_item(self, item_id, count):
        current_date = datetime.now().strftime("%Y-%m-%d")
        chest_item = self.fetch_item_by_id(item_id)

        chest_item["item_cnt"] -= count
        chest_item["date"] = current_date

        if chest_item["item_cnt"] <= 0:
            item_index = self.data["list"].index(chest_item)
            del self.data["list"][item_index]
            self.data["cnt"] -= 1

        self.save()


class ShareManager:
    """Manages the player's Share Shelf.

    Attributes:
        data: A dictionary containing the loaded Share Shelf data.
    """

    def __init__(self):
        self._redundant_fields = {"kinomi", "kinomi_id"}
        self.data = db.read(save_data.gscd, "share_data")

    def update_json(self):
        for item in self.data["share_list"]:
            item_id = item["item_id"]

            item_desc = text.lookup_str("item_descriptions", item_id)

            item["pokeitem"] = text.lookup_str("item", item_id)

            item_sort_data = item_info[str(item_id)]

            item["field_line1"] = item_desc[0]
            item["field_line2"] = item_desc[1]
            item["field_line3"] = item_desc[2]

    def save(self):
        share_data = {
            "cnt": len(self.data["share_list"]),
            "share_list": [
                {k: v for k, v in item.items() if k not in self._redundant_fields}
                for item in self.data["share_list"]
            ]
        }

        db.write(save_data.gscd, "share_data", share_data)

    def fetch_plot_by_id(self, material_id: int):
        return next((p for p in self.data["share_list"] if p["material_id"] == material_id), None)

    def fetch_plot_by_cords(self, x: int, y: int):
        return next((p for p in self.data["share_list"] if p["x"] == x and p["y"] == y), None)

    def share_to_chest(self, material_id: int):
        plot = self.fetch_plot_by_id(material_id)

        plot_index = self.data["share_list"].index(plot)

        pokeitem_id = plot["item_id"]

        item_desc = text.lookup_str("item_descriptions", pokeitem_id)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        share_to_chest_data = {
            "pokeitem_id": plot["item_id"],
            "count": 1
        }

        self.data["share_list"].pop(self.data["share_list"].index(plot))

        self.save()

        return share_to_chest_data

    def place(self, x: int, y: int, item_id: int):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        item_desc = text.lookup_str("item_descriptions", item_id)

        member_savedata_id = save_data.read_player_data()["member"]["member_savedata_id"]

        pgl_name = save_data.read_player_data()["member"]["pgl_name"]

        player_name = save_data.read_player_data()["member"]["player_name"]

        pokemon_name = save_data.read_player_data()["member"]["pokemon_name"]

        pokemon_no = save_data.read_sleeping_pokemon()["pokemon_no"]

        pokemon_nickname = save_data.read_sleeping_pokemon()["pokemon_nickname"]

        form_no = save_data.read_sleeping_pokemon()["form_no"]

        val_1 = x * 10

        val_2 = y

        almost_material_id = 3000 + val_1 + val_2

        material_id = json.dumps(almost_material_id)

        pull_from_chest_data = {
            "item_id": item_id,
            "count": 1
        }

        new_item = {"material_id": material_id, "item_id": item_id, "pokeitem": text.lookup_str("item", item_id), "x": x, "y": y, "history_id": "", "old_member_savedata_id": member_savedata_id, "pokemon_no": pokemon_no, "form_no": form_no, "pokename": pokemon_name, "pgl_name": pgl_name, "nickname": player_name, "poke_nickname": pokemon_nickname, "field_line1": item_desc[0], "field_line2": item_desc[1], "field_line3": item_desc[2], "created_at": current_time, "old_item_id": item_id, "new_item_id": "" , "old_item_name": text.lookup_str("item", item_id)}

        self.data["share_list"].append(new_item)

        self.save()

        return pull_from_chest_data

    def switch_swap(self, material_id: int, member_savedata_id: int, item_id: int):

        plot = self.fetch_plot_by_id(material_id)

        plot_index = self.data["share_list"].index(plot)

        old_item_id = plot["item_id"]

        item_desc = text.lookup_str("item_descriptions", item_id)

        pgl_name = save_data.read_player_data()["member"]["pgl_name"]

        player_name = save_data.read_player_data()["member"]["player_name"]

        pokemon_name = save_data.read_player_data()["member"]["pokemon_name"]

        pokemon_no = save_data.read_sleeping_pokemon()["pokemon_no"]

        pokemon_nickname = save_data.read_sleeping_pokemon()["pokemon_nickname"]

        form_no = save_data.read_sleeping_pokemon()["form_no"]

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        switch_swap_data = {
            "item_id": item_id,
            "old_item_id": old_item_id,
            "count": 1
        }

        self.data["share_list"][plot_index] = {"material_id": material_id, "item_id": item_id, "pokeitem": text.lookup_str("item", item_id), "x": plot["x"], "y": plot["y"], "history_id": "" , "old_member_savedata_id": member_savedata_id, "pokemon_no": pokemon_no, "form_no": form_no, "pokename": pokemon_name, "pgl_name": pgl_name, "nickname": player_name, "poke_nickname": pokemon_nickname, "field_line1": item_desc[0], "field_line2": item_desc[1], "field_line3": item_desc[2], "created_at": current_time, "old_item_id": old_item_id, "new_item_id": item_id , "old_item_name": text.lookup_str("item", old_item_id)}

        self.save()

        return switch_swap_data

class CropManager:
    """Manages the player's Berry garden.

    Attributes:
        data: A dictionary containing the loaded Berry plot data.
    """

    EXPANSION_THRESHOLDS = {
        3: 900,
        4: 2_100,
        5: 3_500,
        6: 10_000,
        7: 20_000,
        8: 30_000,
        9: 50_000,
        10: 100_000,
    }

    def __init__(self):
        self._redundant_fields = {"kinomi", "kinomi_id", "desc1", "desc2", "desc3"}
        self.data = db.read(save_data.gscd, "crop_data")

    def update_json(self):
        for crop in self.data["croft_list"]:
            if "pokeitem_id" not in crop:
                continue

            berry_desc = text.lookup_str("item_descriptions", crop["pokeitem_id"])

            crop["kinomi"] = text.lookup_str("item", crop["pokeitem_id"])
            crop["kinomi_id"] = crop["pokeitem_id"] - 148

            crop["desc1"] = berry_desc[0]
            crop["desc2"] = berry_desc[1]
            crop["desc3"] = berry_desc[2]

    def save(self):
        crop_data = {
            "croft_list": [
                {k: v for k, v in crop.items() if k not in self._redundant_fields}
                for crop in self.data["croft_list"]
            ],
            "diglett_flag": 0
        }

        db.write(save_data.gscd, "crop_data", crop_data)

    def fetch_plot_by_id(self, my_croft_id: int):
        return next((p for p in self.data["croft_list"] if p["my_croft_id"] == my_croft_id), None)

    def water_plot(self, my_croft_id):
        plot = self.fetch_plot_by_id(my_croft_id)
        plot["dirt_hp"] = 100

        self.save()

    def sow(self, my_croft_id: int, pokeitem_id: int):
        plot = self.fetch_plot_by_id(my_croft_id)

        current_time = round(time.time())

        berry_id = pokeitem_id - 148

        berry_desc = text.lookup_str("item_descriptions", pokeitem_id)

        plot.update({
            "my_croft_id": my_croft_id,
            "pokeitem_id": pokeitem_id,
            "kinomi": text.lookup_str("item", pokeitem_id),
            "kinomi_id": berry_id,
            "dirt_hp": 100,
            "kinomi_state": 0,
            "desc1": berry_desc[0],
            "desc2": berry_desc[1],
            "desc3": berry_desc[2],
            "x": plot["x"],
            "y": plot["y"],
            "server": {"planted_at": current_time, "updated_at": current_time, "yield": berry_data[str(berry_id)]["max_yield"]}
        })

        self.save()

    def harvest(self, my_croft_id: int):
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


    def do_garden_expansion(self):
        dream_points = save_data.read_player_data()["member"]["experiment_point"]
        num_crop_rows = len(self.data["croft_list"]) // 3

        threshold = self.EXPANSION_THRESHOLDS.get(num_crop_rows)
        if threshold is not None and dream_points >= threshold:
            db.write(save_data.gscd, "crop_data", {"diglett_flag": 1})


    def process_berry_growth(self):
        current_time = round(time.time())

        for plant in self.data["croft_list"]:
            if "dirt_hp" not in plant:
                continue

            curr_berry_data = berry_data[str(plant["kinomi_id"])]

            hours_since_planted = (current_time - plant["server"]["planted_at"]) // 3600
            hours_since_update = (current_time - plant["server"]["updated_at"]) // 3600

            hours_at_last_update = hours_since_planted - hours_since_update

            single_stage_time = curr_berry_data["grow_time"] / 4

            for hour in range(1, hours_since_update + 1):
                total_hours = hours_at_last_update + hour
                plant["kinomi_state"] = min(total_hours // single_stage_time, 4)

                if plant["dirt_hp"] == 0: #remove 1/5th of the berry's max, but no lower than 2 berries
                    plant["server"]["yield"] = max(plant["server"]["yield"] - (curr_berry_data["max_yield"] * 0.2), 2)
                else:
                    plant["dirt_hp"] -= curr_berry_data["drain_rate"]

            if plant["dirt_hp"] < 0:
                plant["dirt_hp"] = 0

            plant["server"]["updated_at"] = current_time

        self.save()

chest = ChestManager()
crops = CropManager()
share = ShareManager()
