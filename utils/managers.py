"""The player's Treasure Chest and Berry garden.

Managers are loaded fresh from the database by get_chest()/get_crops() on every call.
Every change goes through change(), which re-reads the column, edits it, and writes it
back. `data` is then reloaded, with the display fields the client wants (names,
descriptions, sort keys) added. Those are never stored.
"""
import time
from collections.abc import Callable
from typing import Any, ClassVar

from game_sync_server.entralinked.utility.db_manager import db
from utils import save_data, text
from utils.berries import is_berry, to_berry_id
from utils.constants import SECONDS_PER_HOUR
from utils.data import load_json_data
from utils.models import ChestData, ChestItem, CropData, Plot

ITEM_INFO: dict[str, dict] = load_json_data("items")
BERRY_INFO: dict[str, dict] = load_json_data("berries")  # its keys are kinomi_id values written as strings


class _ColumnManager:
    """One JSON column of a player's save.

    `data` is the column plus display fields.
    """

    COLUMN: ClassVar[str]

    def __init__(self, gscd: str) -> None:
        self._gscd = gscd
        self.data = self._with_display_fields(db.read(gscd, self.COLUMN))

    def _with_display_fields(self, stored: Any) -> Any:
        """Add the display fields to freshly read data, in place, and return it."""
        raise NotImplementedError

    def _update_counters(self, stored: Any) -> None:
        """Fix the counters stored in the column after an edit."""

    def change(self, edit: Callable[[Any], Any]) -> Any:
        """Apply `edit` to the column and save it in a single write.

        `edit` sees the column as it is in the database right now (without display fields).
        Return what `edit` returned. Nothing is saved if it raises. `data` is reloaded
        afterwards.
        """
        result = None

        def apply(stored: dict) -> None:
            nonlocal result
            result = edit(stored)
            self._update_counters(stored)

        self.data = self._with_display_fields(db.update(self._gscd, self.COLUMN, apply))
        return result


def _stack_of(chest: ChestData, item_id: int) -> ChestItem | None:
    return next((item for item in chest["list"] if item["pokeitem_id"] == item_id), None)


class ChestManager(_ColumnManager):
    """The player's Treasure Chest."""

    COLUMN = "chest_data"
    data: ChestData

    def _update_counters(self, stored: ChestData) -> None:
        stored["cnt"] = len(stored["list"])

    def _with_display_fields(self, stored: ChestData) -> ChestData:
        for item in stored["list"]:
            item_id = item["pokeitem_id"]
            sort_info = ITEM_INFO[str(item_id)]
            line1, line2, line3, *_ = text.lookup_description("item_descriptions", item_id)
            item.update({
                "pokeitem":       text.lookup_str("item", item_id),
                "bunrui_no":      sort_info["first_sort"],
                "b_hozon_sentou": sort_info["second_sort"],
                "field_line1":    line1,
                "field_line2":    line2,
                "field_line3":    line3,
            })
        return stored

    def fetch_item_by_id(self, item_id: int) -> ChestItem | None:
        """Return the chest's stack of this item, if it has any."""
        return _stack_of(self.data, item_id)

    def add_item(self, item_id: int, count: int) -> None:
        """Add `count` of an item."""
        self.move_items({item_id: count})

    def move_items(self, changes: dict[int, int]) -> dict[int, int]:
        """Add items (positive counts) and take items out (negative counts) in a single write.

        Taking out cannot remove more than the chest has.
        """
        def move(chest: ChestData) -> dict[int, int]:
            today = save_data.today_jst_str()
            moved = {}
            for item_id, count in changes.items():
                stack = _stack_of(chest, item_id)
                if count < 0:
                    count = -min(-count, stack["item_cnt"] if stack else 0)
                if not count:
                    continue
                if stack is None:
                    stack = {"pokeitem_id": item_id, "item_cnt": 0}
                    chest["list"].append(stack)
                stack["item_cnt"] += count
                stack["date"] = today
                if stack["item_cnt"] <= 0:
                    chest["list"].remove(stack)
                moved[item_id] = count
            return moved

        return self.change(move)

    def remove_item(self, item_id: int, count: int) -> None:
        """Remove `count` of an item.

        Raise ValueError, and remove nothing, if the chest has fewer than that.
        """
        self.remove_items(((item_id, count),))

    def remove_items(self, counts: tuple[tuple[int, int], ...]) -> None:
        """Remove several items at once.

        `counts` holds (item id, count) pairs, and counts of 0 are ignored. Raise ValueError,
        and remove nothing, if the chest has too few of any item.
        """
        def remove(chest: ChestData) -> None:
            stacks: list[tuple[ChestItem, int]] = []
            for item_id, count in counts:
                if not count:
                    continue
                stack = _stack_of(chest, item_id)
                have = stack["item_cnt"] if stack else 0
                if stack is None or have < count:
                    raise ValueError(f"Has {have} of item {item_id}, needs {count}")
                stacks.append((stack, count))

            for stack, count in stacks:
                stack["item_cnt"] -= count
                stack["date"] = save_data.today_jst_str()
                if stack["item_cnt"] <= 0:
                    chest["list"].remove(stack)

        self.change(remove)

    def convert_stale_berries(self, points_per_berry: int) -> int:
        """Reduce every Berry stack down to 1, converting the surplus to Dream Points.

        Return the Dream Points awarded.
        """
        def convert(chest: ChestData) -> int:
            berries_converted = 0
            for item in chest["list"]:
                surplus = item["item_cnt"] - 1
                if is_berry(item["pokeitem_id"]) and surplus > 0:
                    berries_converted += surplus
                    item["item_cnt"] = 1
            return berries_converted

        return self.change(convert) * points_per_berry


def _plot_of(garden: CropData, my_croft_id: int) -> Plot:
    plot = next((p for p in garden["croft_list"] if p["my_croft_id"] == my_croft_id), None)
    if plot is None:
        raise ValueError(f"No garden plot {my_croft_id}")
    return plot


class CropManager(_ColumnManager):
    """The player's Berry garden (the crop_data column)."""

    COLUMN = "crop_data"
    data: CropData
    PLOTS_PER_ROW = 3
    GROWTH_STAGES = 4
    FULL_DIRT_HP = 100
    FULL_BERRY_HP = 5
    HOURS_PER_DRAIN = 3  # the soil loses the Berry's whole drain_rate every 3rd hour
    MIN_YIELD = 2
    # rows of plots -> Dream Points needed for Diglett to add the next row
    EXPANSION_THRESHOLDS: ClassVar[dict[int, int]] = {
        3: 900,
        4: 2_100,
        5: 3_500,
        6: 10_000,
        7: 20_000,
        8: 30_000,
        9: 50_000,
        10: 100_000
    }

    def _with_display_fields(self, stored: CropData) -> CropData:
        for plot in stored["croft_list"]:
            if "pokeitem_id" in plot:
                item_id = plot["pokeitem_id"]
                desc1, desc2, desc3, *_ = text.lookup_description("item_descriptions", item_id)
                plot.update({
                    "kinomi":    text.lookup_str("item", item_id),
                    "kinomi_id": to_berry_id(item_id),
                    "desc1":     desc1,
                    "desc2":     desc2,
                    "desc3":     desc3,
                })
        return stored

    def fetch_plot_by_id(self, my_croft_id: int) -> Plot:
        """Return the plot with this id. Raise ValueError if the garden has no such plot."""
        return _plot_of(self.data, my_croft_id)

    def water_plot(self, my_croft_id: int) -> None:
        """Refill a plot's soil. Raise ValueError if nothing is planted in it."""
        def water(garden: CropData) -> None:
            plot = _plot_of(garden, my_croft_id)
            if "server" not in plot:
                raise ValueError(f"Nothing is planted in garden plot {my_croft_id}")

            self._grow_all(garden)  # count the hours it spent dry before resetting the clock
            plot["dirt_hp"] = self.FULL_DIRT_HP
            plot["server"]["watered_at"] = round(time.time())

        self.change(water)

    def sow(self, my_croft_id: int, pokeitem_id: int) -> None:
        """Plants a Berry in a freshly watered plot."""
        def plant(garden: CropData) -> None:
            now = round(time.time())
            _plot_of(garden, my_croft_id).update({
                "pokeitem_id":  pokeitem_id,
                "dirt_hp":      self.FULL_DIRT_HP,
                "kinomi_state": 0,
                "server": {"planted_at": now, "updated_at": now, "watered_at": now,
                           "berry_hp": self.FULL_BERRY_HP},
            })

        self.change(plant)

    def harvest(self, my_croft_id: int) -> dict:
        """Empty a plot and return what it gave (the kinomi_harvesting response).

        Raise ValueError if nothing is planted in it.
        """
        def pick(garden: CropData) -> dict:
            plot = _plot_of(garden, my_croft_id)
            if "pokeitem_id" not in plot:
                raise ValueError(f"Nothing is planted in garden plot {my_croft_id}")

            pokeitem_id = plot["pokeitem_id"]
            harvest_data = {
                "kinomi_id":   to_berry_id(pokeitem_id),
                "kinomi":      text.lookup_str("item", pokeitem_id),
                "pokeitem_id": pokeitem_id,
                "count":       self.harvest_yield(plot),
            }
            empty_plot: Plot = {"my_croft_id": my_croft_id, "x": plot["x"], "y": plot["y"]}
            garden["croft_list"][garden["croft_list"].index(plot)] = empty_plot
            return harvest_data

        return self.change(pick)

    def check_garden_expansion(self) -> None:
        """Set diglett_flag in the response data if Diglett can add a row of plots.

        That is when the player has enough Dream Points for the next row.
        """
        dream_points = save_data.read_member(self._gscd).get("experiment_point") or 0
        threshold = self.EXPANSION_THRESHOLDS.get(len(self.data["croft_list"]) // self.PLOTS_PER_ROW)
        if threshold is not None and dream_points >= threshold:
            self.data["diglett_flag"] = 1

    @classmethod
    def hours_until_dry(cls, drain_rate: int) -> int:
        """Whole hours after watering until the soil reaches 0."""
        drains_needed = -(-cls.FULL_DIRT_HP // drain_rate)  # rounded up
        return drains_needed * cls.HOURS_PER_DRAIN

    @classmethod
    def harvest_yield(cls, plot: Plot) -> int:
        """Return the number of Berries a plot gives.

        That is an equal share of max_yield for each point of berry HP left, at least
        MIN_YIELD.
        """
        berry = BERRY_INFO[str(to_berry_id(plot["pokeitem_id"]))]
        return max(berry["max_yield"] // cls.FULL_BERRY_HP * plot["server"]["berry_hp"], cls.MIN_YIELD)

    def process_berry_growth(self) -> None:
        """Advances every planted Berry by the whole hours since its last update.

        The soil loses the Berry's whole drain_rate every 3rd hour after watering, and (as
        in Platinum) each whole hour it spends dry costs 1 of the Berry's 5 HP. Once the
        Berry fruits, the soil stops drying and its HP (and so its yield) is fixed.
        """
        self.change(self._grow_all)

    def _grow_all(self, garden: CropData) -> None:
        now = round(time.time())
        for plot in garden["croft_list"]:
            if "dirt_hp" in plot:
                self._grow(plot, now)

    def _grow(self, plot: Plot, now: int) -> None:
        """Advances one planted Berry to `now`.

        dirt_hp and the dry hours are worked out from the time since watering rather than
        subtracted step by step, so the leftover part-hours between updates are never lost.
        """
        growth = plot["server"]
        hours = (now - growth["updated_at"]) // SECONDS_PER_HOUR
        if hours <= 0:
            return
        processed_until = growth["updated_at"] + hours * SECONDS_PER_HOUR

        berry = BERRY_INFO[str(to_berry_id(plot["pokeitem_id"]))]
        hours_since_planted = (now - growth["planted_at"]) // SECONDS_PER_HOUR
        hours_per_stage = berry["grow_time"] / self.GROWTH_STAGES
        plot["kinomi_state"] = min(int(hours_since_planted // hours_per_stage), self.GROWTH_STAGES)

        # nothing dries once it has fruited
        fruited_at = growth["planted_at"] + berry["grow_time"] * SECONDS_PER_HOUR
        drying_until = min(now, fruited_at)

        drain_rate = berry["drain_rate"]
        hours_since_watered = max((drying_until - growth["watered_at"]) // SECONDS_PER_HOUR, 0)
        drains = hours_since_watered // self.HOURS_PER_DRAIN
        plot["dirt_hp"] = max(self.FULL_DIRT_HP - drains * drain_rate, 0)

        dry_at = growth["watered_at"] + self.hours_until_dry(drain_rate) * SECONDS_PER_HOUR

        def dry_hours_by(timestamp: int) -> int:
            """Whole hours the soil had been dry for at `timestamp`."""
            return max((min(timestamp, fruited_at) - dry_at) // SECONDS_PER_HOUR, 0)

        newly_dry = dry_hours_by(processed_until) - dry_hours_by(growth["updated_at"])
        growth["berry_hp"] = max(growth["berry_hp"] - newly_dry, 0)

        # keep the leftover part of an hour for next time
        growth["updated_at"] = processed_until


def get_chest(gscd: str | None = None) -> ChestManager:
    """Return the Treasure Chest of `gscd`, or of the logged-in player."""
    return ChestManager(save_data.require_gscd(gscd))


def get_crops(gscd: str | None = None) -> CropManager:
    """Return the Berry garden of `gscd`, or of the logged-in player."""
    return CropManager(save_data.require_gscd(gscd))
