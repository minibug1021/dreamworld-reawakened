import sys
import json
from pathlib import Path
try:
    from PyQt5 import QtWidgets, QtGui, QtCore, uic
except ImportError:
    PyQt5 = None
    try:
        from PyQt6 import QtWidgets, QtGui, QtCore, uic
        from PyQt6.QtWidgets import QLabel
    except ImportError:
        print("Error: PyQt5 or PyQt6 is required to run this application.")
        sys.exit(1)

import extra_data
import load_save_gen5

ROOT_DIR = Path(__file__).resolve().parent

type_colors = {
    None:       "lightgray",
    "Normal":   "#ada594",
    "Fighting": "#a55239",
    "Flying":   "#9cadf7",
    "Poison":   "#b55aa5",
    "Ground":   "#d6b55a",
    "Rock":     "#bda55a",
    "Bug":      "#adbd21",
    "Ghost":    "#6363b5",
    "Steel":    "#adadc6",
    "Fire":     "#f75231",
    "Water":    "#399cff",
    "Grass":    "#7bce52",
    "Electric": "#ffc631",
    "Psychic":  "#ff73a5",
    "Ice":      "#5acee7",
    "Dragon":   "#7b63e7",
    "Dark":     "#735a4a",
}

GENDER_STYLES = {
    0: ("♂", "color: #3355FF;"),
    1: ("♀", "color: #FF77DD;"),
}


class PkmnSpriteEntry(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal(str)

    DEFAULT_STYLE   = "border: 3px solid #444; border-radius: 10px; background: white;"
    HOVER_STYLE     = "border: 3px solid #777; border-radius: 10px; background: #f0f0f0;"
    HIGHLIGHT_STYLE = "border: 3px solid #4A90E2; border-radius: 10px; background: #dcecff;"
    EMPTY_STYLE     = "border: 3px solid #ccc; border-radius: 10px; background: #e8e8e8;"

    def __init__(self, image_path, width, height, name):
        super().__init__()
        self.name = name
        self.is_selected = False
        self.is_empty = image_path is None

        if self.is_empty:
            self.setStyleSheet(self.EMPTY_STYLE)
        else:
            pixmap = QtGui.QPixmap(str(image_path)).scaled(
                width, height,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.FastTransformation,
            )
            self.setPixmap(pixmap)
            self.setStyleSheet(self.DEFAULT_STYLE)

        self.setFixedSize(width, height)
        self.setAlignment(QtCore.Qt.AlignCenter)

    def setSelected(self, is_selected):
        self.is_selected = is_selected
        self.setStyleSheet(self.HIGHLIGHT_STYLE if is_selected else self.DEFAULT_STYLE)

    def mousePressEvent(self, event):
        if not self.is_empty and event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.name)

    def enterEvent(self, event):
        if not self.is_empty and not self.is_selected:
            self.setStyleSheet(self.HOVER_STYLE)

    def leaveEvent(self, event):
        if not self.is_empty and not self.is_selected:
            self.setStyleSheet(self.DEFAULT_STYLE)


class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(ROOT_DIR / "pkmn_manager.ui", self)

        self.selected_sprite = None
        self.party_sprites = {}
        self.storage_sprites = {}
        self.selected_box = 1

        self.partyGrid.setSpacing(1)
        self.storageGrid.setSpacing(1)

        self.box_data.currentIndexChanged.connect(self.changeBox)
        self.load_save.clicked.connect(self.select_save_file)
        self.send_DW.setEnabled(False)
        self.send_DW.clicked.connect(self.send_to_DW)

        self.ball_image = QtWidgets.QLabel()
        self.ball_image.setFixedWidth(24)
        self.species_info.insertWidget(2, self.ball_image)

        self.setFixedSize(self.size())
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #888;
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
                font-family: "Roboto";
                font-size: 18px;
                background: #f5f5f5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLineEdit {
                font-family: "Monospace", monospace;
                font-size: 16px;
            }
            QComboBox {
                font-family: "Monospace";
                font-size: 18px;
            }
        """)

    # --- helpers ---

    @staticmethod
    def _get_form_str(pkmn):
        if pkmn.natdex in (493, 649):
            return ""
        if pkmn.natdex in (521, 592, 593) and pkmn.gender == 1:
            return "-1"
        return f"-{pkmn.form}" if pkmn.form else ""

    @staticmethod
    def _set_gender_label(label, gender_val):
        symbol, style = GENDER_STYLES.get(gender_val, (None, "color: black;"))
        label.setText(symbol)
        label.setStyleSheet(style)

    @staticmethod
    def _set_optional_field(widget, value):
        if value:
            widget.setText(str(value))
            widget.setStyleSheet("background: white;")
        else:
            widget.setText(None)
            widget.setStyleSheet("background: lightgray;")

    # --- save file ---

    def select_save_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Save File", "", "Save Files (*.sav);;All Files (*)"
        )
        if not file_path:
            return

        self.save_path.setText(file_path)
        self.sf = load_save_gen5.SaveFile(file_path)
        self.tr_data = self.sf.trainer()

        self.box_data.clear()
        box_layout = self.sf.box_layout()
        for i in range(box_layout.num_boxes):
            self.box_data.addItem(f"#{i + 1} — {box_layout.get_box_name(i)}")

        self.load_save.setEnabled(False)

        self.clear_layout(self.partyGrid)
        self.clear_layout(self.storageGrid)

        self._populate_grid(self.partyGrid,   "party",   rows=3, cols=2)
        self._populate_grid(self.storageGrid, "storage", rows=5, cols=6)

        self.init_trainer_data(self.tr_data)

    def init_trainer_data(self, trainer):
        self.save_trainer_name.setText(trainer.name)
        self._set_optional_field(self.country, trainer.country)
        self._set_optional_field(self.region, trainer.region)
        self.language.setText(extra_data.language[trainer.language])
        self.version.setText(extra_data.version[trainer.game])
        self._set_gender_label(self.save_trainer_gender, 0 if trainer.gender == "Male" else 1)
        self.num_badges.setText(str(trainer.num_badges))

    # --- grids ---

    def _get_pokemon(self, grid_type, index):
        if grid_type == "party":
            return self.sf.get_party_pokemon(slot=index)
        return self.sf.get_box_pokemon(box=self.selected_box, slot=index)

    def _populate_grid(self, layout, grid_type, rows, cols):
        sprites = {}
        for slot, (r, c) in enumerate(
            (r, c) for r in range(rows) for c in range(cols)
        ):
            pkmn = self._get_pokemon(grid_type, slot)

            if pkmn.natdex == 0:
                sprite = PkmnSpriteEntry(None, 64, 64, f"{grid_type}_{slot}")
            else:
                form_str = self._get_form_str(pkmn)
                image_path = ROOT_DIR / "sprites" / "pokemon" / f"{pkmn.natdex}{form_str}.png"
                sprite = PkmnSpriteEntry(str(image_path), 64, 64, f"{grid_type}_{slot}")
                sprite.clicked.connect(self.on_sprite_clicked)

            layout.addWidget(sprite, r, c)
            sprites[slot] = sprite

        if grid_type == "party":
            self.party_sprites = sprites
        else:
            self.storage_sprites = sprites

    def changeBox(self):
        self.selected_box = self.box_data.currentIndex() + 1
        self.selected_sprite = None
        self.clear_layout(self.storageGrid)
        self.storage_sprites = {}
        self._populate_grid(self.storageGrid, "storage", rows=5, cols=6)

    @staticmethod
    def clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()

    # --- actions ---

    def on_sprite_clicked(self, name):
        grid_type, index = name.split("_")
        index = int(index)

        if self.selected_sprite:
            self.selected_sprite.setSelected(False)

        sprites = self.party_sprites if grid_type == "party" else self.storage_sprites
        self.selected_sprite = sprites.get(index)

        if not self.selected_sprite:
            return

        self.selected_sprite.setSelected(True)
        self.send_DW.setEnabled(True)
        pkmn = self._get_pokemon(grid_type, index)

        self.natdex.setText(f"{pkmn.natdex:03d}")
        self.species.setText(pkmn.species)
        self.ball_image.setPixmap(
            QtGui.QPixmap(str(ROOT_DIR / "sprites" / "balls" / f"{pkmn.ball}.png"))
        )
        self.level.setText(str(pkmn.level))
        self.trainer_name.setText(pkmn.trainer_name)
        self.nature.setText(pkmn.nature)

        self._set_gender_label(self.pkmn_gender, pkmn.gender)
        self._set_gender_label(self.trainer_gender, pkmn.trainer_gender)

        form_key = f"{pkmn.natdex}-{pkmn.form}"
        self._set_optional_field(self.form, extra_data.form_names.get(form_key))

        nickname = pkmn.nickname if pkmn.nickname != pkmn.species else None
        self._set_optional_field(self.nickname, nickname)

        self.type1.setText(pkmn.type1)
        self.type1.setStyleSheet(f"background: {type_colors[pkmn.type1]};")
        self.type2.setText(pkmn.type2)
        self.type2.setStyleSheet(f"background: {type_colors[pkmn.type2]};")

    def send_to_DW(self):
        if not self.selected_sprite:
            return

        grid_type, index = self.selected_sprite.name.split("_")
        index = int(index)
        pkmn = self._get_pokemon(grid_type, index)

        self.selected_sprite.setSelected(False)

        SAVE_DATA_DIR = ROOT_DIR.parent / "save_data"

        with open(SAVE_DATA_DIR / "player_data.json", "r", encoding="UTF-8") as f:
            player_data = json.load(f)

        player_data["member"].update({ #at the moment 220 is the only support country ID for things like the Dream Pal map
            "country_id":          "220", #str(extra_data.country.index(self.tr_data.country))
            "send_pokemon_count":  player_data["member"]["send_pokemon_count"] + 1,
            "rom_id":              self.tr_data.game,
            "rom_name":            extra_data.version[self.tr_data.game],
            "player_badge_num":    str(self.tr_data.num_badges),
            "alter_rom_name":      self.tr_data.name,
            "langcode":            self.tr_data.language,
            "pokemon_no":          str(pkmn.natdex),
            "pokemon_name":        pkmn.species,
            "form_no":             str(pkmn.form),
            "type1":               pkmn.type1,
            "type2":               pkmn.type2,
        })

        pokemon_data = {
            "pokemon_no":       pkmn.natdex,
            "pokemon_name":     pkmn.species,
            "form_no":          str(pkmn.form),
            "type1":            pkmn.type1,
            "type2":            pkmn.type2,
            "pokemon_nickname": pkmn.nickname if pkmn.nickname != pkmn.species else None,
            "oyaname":          pkmn.trainer_name,
            "level":            pkmn.level,
            "sex":              pkmn.gender,
            "personality":      pkmn.nature,
            "ball_name":        pkmn.ball,
        }

        with open(SAVE_DATA_DIR / "player_data.json", "w+", encoding="UTF-8") as f:
            json.dump(player_data, f, indent=2, ensure_ascii=False)

        with open(SAVE_DATA_DIR / "sleeping_pokemon.json", "w+", encoding="UTF-8") as f:
            json.dump(pokemon_data, f, indent=2, ensure_ascii=False)

        self.send_DW.setEnabled(False)
        self.done.setText("Done!")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_() if PyQt5 else app.exec())