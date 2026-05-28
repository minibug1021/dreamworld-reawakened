import sys
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QTextEdit, QSpinBox, QDoubleSpinBox, QLineEdit, QLabel, QSizePolicy, QMainWindow
from dataclasses import dataclass

@dataclass
class StringEntry:
    string_id: str = ""
    text_string: str = ""
    size: int = 0
    letterSpacing: float = 0.0
    leading: int = 0
    color: str = ""
    is_translated: bool = False
    bold: bool = False
    path: str = ""

class XMLLineEditWidget(QWidget):
    def __init__(self, entry: StringEntry, comparison_text: str | None = None, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.has_comparison_str = comparison_text is not None
        self.comparison_text = comparison_text or ""
        self._setup_ui()
        self.load(self.entry)

    def load(self, entry: StringEntry):
        self.string_id.setText(entry.string_id)
        self.text_string.setPlainText(entry.text_string)
        if self.has_comparison_str:
            self.text_comparison.setPlainText(self.comparison_text)
        self.text_size.setValue(int(entry.size))
        self.letter_spacing.setValue(float(entry.letterSpacing))
        self.leading.setValue(int(entry.leading))
        self.text_color.setText(entry.color)
        self.is_translated.setChecked(entry.is_translated)
        self.is_text_bold.setChecked(entry.bold)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._build_toolbar_row())
        main_layout.addLayout(self._build_top_row())

        self.text_string.textChanged.connect(lambda: setattr(self.entry, "text_string", self.text_string.toPlainText().replace("↵\n", "\n")))
        self.text_size.valueChanged.connect(lambda v: setattr(self.entry, "size", v))
        self.letter_spacing.valueChanged.connect(lambda v: setattr(self.entry, "letterSpacing", v))
        self.leading.valueChanged.connect(lambda v: setattr(self.entry, "leading", v))
        self.text_color.textChanged.connect(lambda v: setattr(self.entry, "color", v))
        self.is_translated.checkStateChanged.connect(lambda v: setattr(self.entry, "is_translated", v == Qt.CheckState.Checked))
        self.is_text_bold.checkStateChanged.connect(lambda v: setattr(self.entry, "bold", v == Qt.CheckState.Checked))

    def _build_top_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(4)

        # --- text editor ---
        self.text_string = QTextEdit()
        self.text_string.setFixedHeight(90)

        layout.addWidget(self.text_string)

        # --- text comparison widget ---
        if self.has_comparison_str:
            self.text_comparison = QTextEdit()
            self.text_comparison.setFixedHeight(90)
            self.text_comparison.setReadOnly(True)
            self.text_comparison.setStyleSheet("QTextEdit { color: gray }")
            layout.addWidget(self.text_comparison)

        return layout

    def _build_toolbar_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)

        # --- string id ---
        self.string_id = QLabel("test")
        font = self.string_id.font()
        font.setPointSize(16)
        font.setBold(True)
        self.string_id.setFont(font)

        # --- translated toggle ---
        self.is_translated = QCheckBox()
        self.is_translated.setToolTip("Indicates that the text is a translation and not the original string.")
        self.is_translated.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # --- text size ---
        self.text_size = QSpinBox()
        self.text_size.setToolTip("The size in pixels of text in this text format.")
        self.text_size.setRange(0, 30)

        # --- letter spacing ---
        self.letter_spacing = QDoubleSpinBox()
        self.letter_spacing.setToolTip("A number representing the amount of space that is uniformly distributed between all characters.")
        self.letter_spacing.setRange(-999.0, 999.0)
        self.letter_spacing.setSingleStep(0.05)
        self.letter_spacing.setDecimals(2)

        # --- leading ---
        self.leading = QSpinBox()
        self.leading.setToolTip("An integer representing the amount of vertical space (called leading) between lines.")
        self.leading.setRange(-999, 999)

        # --- text color ---
        self.text_color = QLineEdit()
        self.text_color.setToolTip("Indicates the color of the text.")
        self.text_color.setPlaceholderText("#FFFFFF")
        self.text_color.setMaxLength(7)
        self.text_color.setFixedWidth(80)

        # --- bold toggle ---
        self.is_text_bold = QCheckBox("Bold")
        self.is_text_bold.setToolTip("Specifies whether the text is boldface.")

        # -------
        # Signals
        # -------

        self.text_color.textChanged.connect(self._fix_uppercase)

        # ------
        # Layout
        # ------

        layout.addStretch()

        layout.addWidget(self.string_id)

        layout.addStretch()

        layout.addWidget(QLabel("Translation?"))
        layout.addWidget(self.is_translated)

        layout.addWidget(QLabel("Size"))
        layout.addWidget(self.text_size)

        layout.addWidget(QLabel("Letter Spacing"))
        layout.addWidget(self.letter_spacing)

        layout.addWidget(QLabel("Leading"))
        layout.addWidget(self.leading)

        layout.addWidget(self.text_color)

        layout.addWidget(self.is_text_bold)

        layout.addStretch()

        return layout

    # -------
    # Helpers
    # -------

    def _fix_uppercase(self, text: str):
        if text != text.upper():
            self.text_color.blockSignals(True)
            pos = self.text_color.cursorPosition()
            self.text_color.setText(text.upper())
            self.text_color.setCursorPosition(pos)
            self.text_color.blockSignals(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("xml.ui", self)

        # dict[file][string_id][lang] -> StringEntry
        self.entry_list = {}

        self.languages = {
            "English": "en",
            "Japanese": "ja",
            "French": "fr",
            "Italian": "it",
            "German": "de",
            "Spanish": "es",
            "Korean": "ko"
        }

        self.string_entry_defaults = {
            "size": 0,
            "letterSpacing": 0.0,
            "leading": 0,
            "color": "",
            "bold": False,
        }

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        with open("text.json", "r", encoding="UTF-8") as f:
            self.text_data = json.load(f)

        for xml_file in self.text_data.keys():
            self.sel_file.addItem(xml_file)

        for language in self.languages.keys():
            self.sel_language.addItem(language)
            self.sel_ref_language.addItem(language)

        self._init_cache()
        self._add_widgets()

        self.sel_file.currentTextChanged.connect(self._refresh_widgets)
        self.sel_language.currentTextChanged.connect(self._refresh_widgets)
        self.sel_ref_language.currentTextChanged.connect(self._refresh_widgets)

        self.save_btn.pressed.connect(self.export_entries)
        self.save_btn.pressed.connect(self.save_json)

    def _init_cache(self):

        for file, strings in self.text_data.items():
            self.entry_list[file] = {}

            for string_id, string_data in strings.items():
                if string_id == "path":
                    continue

                self.entry_list[file][string_id] = {}

                for lang_code in self.languages.values():

                    if not string_data[lang_code]:
                        entry = StringEntry(string_id=string_id)
                    else:
                        entry = StringEntry(
                            string_id=string_id,
                            text_string=string_data[lang_code]["string"],
                            is_translated=string_data[lang_code]["is_translation"]
                        )

                    if "path" in strings:
                        entry.path = strings["path"].replace("/../", f"/{lang_code}/")

                    if "format" in string_data:
                        for field, value in string_data["format"].items():
                            setattr(entry, field, value)

                    self.entry_list[file][string_id][lang_code] = entry

    def _refresh_widgets(self):
        self._clear_widgets()
        self._add_widgets()

    def _add_widgets(self):
        file = self.sel_file.currentText()
        sel_lang = self.languages[self.sel_language.currentText()]
        ref_lang = self.languages[self.sel_ref_language.currentText()]
        show_comparison = sel_lang != ref_lang

        for lang_entries in self.entry_list[file].values():
            entry = lang_entries[sel_lang]
            comparison_text = lang_entries[ref_lang].text_string if show_comparison else ""
            widget = XMLLineEditWidget(entry, comparison_text if show_comparison else None)
            self.layout.addWidget(widget)

        self.scrollArea.setWidget(self.container)

    def _clear_widgets(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def export_entries(self):
        BASE_PATH = Path("../DreamWorld_data")

        entries_by_path: dict[str, list[StringEntry]] = {}

        for string_ids in self.entry_list.values():
            for lang_entries in string_ids.values():
                for entry in lang_entries.values():
                    if not entry.path:
                        continue
                    entries_by_path.setdefault(entry.path, []).append(entry)

        for rel_path, entries in entries_by_path.items():
            output_path = BASE_PATH / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            lang_code = Path(rel_path).parts[-3]
            locale = lang_code

            is_format_file = "format" in output_path.stem

            root = ET.Element("data", locale=locale)

            for entry in entries:
                el = ET.SubElement(root, "string", id=entry.string_id)

                if is_format_file:
                    # only write attributes that differ from their defaults
                    if entry.size != self.string_entry_defaults["size"]:
                        el.set("size", str(entry.size))
                    if entry.letterSpacing != self.string_entry_defaults["letterSpacing"]:
                        el.set("letterSpacing", str(entry.letterSpacing))
                    if entry.leading != self.string_entry_defaults["leading"]:
                        el.set("leading", str(entry.leading))
                    if entry.color != self.string_entry_defaults["color"]:
                        el.set("color", entry.color)
                    if entry.bold != self.string_entry_defaults["bold"]:
                        el.set("bold", "true")
                else:
                    if entry.is_translated:
                        el.set("unofficial", "true")
                    # fall back to string_id if text is empty
                    el.text = entry.text_string or entry.string_id

            ET.indent(root, space="\t")

            with output_path.open("w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="utf-8" ?>\n')
                f.write(ET.tostring(root, encoding="unicode", short_empty_elements=is_format_file))

    def save_json(self):
        for file, string_ids in self.entry_list.items():
            for string_id, lang_entries in string_ids.items():
                for lang_code, entry in lang_entries.items():
                    string_data = self.text_data[file][string_id]

                    #existing text update
                    if string_data[lang_code]:
                        #if the string is cleared, clear the JSON as well
                        if entry.text_string == "":
                            string_data[lang_code] = {}

                        else:
                            string_data[lang_code]["string"] = entry.text_string
                            string_data[lang_code]["is_translation"] = entry.is_translated

                    #new text addition
                    elif entry.text_string:
                        string_data[lang_code] = {
                            "string": entry.text_string,
                            "is_translation": entry.is_translated,
                        }

                    # update format fields, removing any that have reverted to their default
                    string_data.setdefault("format", {})
                    for field in ("size", "letterSpacing", "leading", "color", "bold"):
                        value = getattr(entry, field)
                        if value != self.string_entry_defaults[field]:
                            string_data["format"][field] = value
                        else:
                            string_data["format"].pop(field, None)

                    # remove the format block entirely if nothing is set
                    if not string_data["format"]:
                        string_data.pop("format", None)

        with open("text.json", "w", encoding="UTF-8") as f:
            json.dump(self.text_data, f, ensure_ascii=False, indent=4)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
