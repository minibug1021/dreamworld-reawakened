import sys
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
            self.entry = entry

            # group the input widgets to block their signals
            input_widgets = [
                self.text_string, self.text_size, self.letter_spacing,
                self.leading, self.text_color, self.is_translated, self.is_text_bold
            ]

            for w in input_widgets:
                w.blockSignals(True)

            # update UI
            self.string_id.setText(entry.string_id)
            self.text_string.setPlainText(entry.text_string)

            # toggle visibility of comparison panel
            self.text_comparison.setVisible(self.has_comparison_str)
            if self.has_comparison_str:
                self.text_comparison.setPlainText(self.comparison_text)

            self.text_size.setValue(int(entry.size))
            self.letter_spacing.setValue(float(entry.letterSpacing))
            self.leading.setValue(int(entry.leading))
            self.text_color.setText(entry.color)
            self.is_translated.setChecked(entry.is_translated)
            self.is_text_bold.setChecked(entry.bold)

            # unblock signals
            for w in input_widgets:
                w.blockSignals(False)

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
            self.text_comparison = QTextEdit()
            self.text_comparison.setFixedHeight(90)
            self.text_comparison.setReadOnly(True)
            self.text_comparison.setStyleSheet("QTextEdit { color: gray }")
            layout.addWidget(self.text_comparison)

            # hide by default
            self.text_comparison.setVisible(self.has_comparison_str)

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
    SOURCE_ROOTS = [
        "../DreamWorld_data/src/swf/pdw/assets/{lang}/xml",
        "../DreamWorld_data/src/swf/theme/assets/{lang}/xml",
    ]

    def __init__(self):
        super().__init__()
        uic.loadUi("xml.ui", self)

        # dict[file_key][string_id][lang_code] -> StringEntry
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

        self.default_entry = StringEntry()

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        self._init_cache()

        for file_key in self.entry_list.keys():
            self.sel_file.addItem(file_key)

        for language in self.languages.keys():
            self.sel_language.addItem(language)
            self.sel_ref_language.addItem(language)

        self._add_widgets()

        self.sel_file.currentTextChanged.connect(self._refresh_widgets)
        self.sel_language.currentTextChanged.connect(self._refresh_widgets)
        self.sel_ref_language.currentTextChanged.connect(self._refresh_widgets)

        self.save_btn.pressed.connect(self.export_entries)

    # -------------------
    # XML loading helpers
    # -------------------

    @staticmethod
    def _fix_color_str(color: str) -> str:
        if color == "#000000": return "00000000"
        if color == "00000000": return "#000000"

        return f"0x{color[1:]}" if color.startswith("#") else f"#{color[2:]}"

    @staticmethod
    def _parse_strings_xml(path: Path) -> dict[str, dict]:
        result = {}
        try:
            root = ET.parse(path).getroot()

        except ET.ParseError:
            return result

        for el in root.findall("string"):
            sid = el.get("id", "")

            if not sid:
                continue

            result[sid] = {
                "string": el.text or "",
                "is_translation": el.get("unofficial", "false").lower() == "true",
            }

        return result

    @staticmethod
    def _parse_format_xml(path: Path) -> dict[str, dict]:
        result = {}
        try:
            root = ET.parse(path).getroot()

        except ET.ParseError:
            return result

        for el in root.findall("string"):
            sid = el.get("id", "")

            if not sid:
                continue

            fmt = {}

            if el.get("size") is not None:
                fmt["size"] = int(el.get("size"))

            if el.get("letterSpacing") is not None:
                fmt["letterSpacing"] = float(el.get("letterSpacing"))

            if el.get("leading") is not None:
                fmt["leading"] = int(el.get("leading"))

            if el.get("color") is not None:
                fmt["color"] = MainWindow._fix_color_str(el.get("color"))

            if el.get("bold") is not None:
                fmt["bold"] = el.get("bold").lower() == "true"

            result[sid] = fmt

        return result

    def _init_cache(self) -> None:
        lang_codes = list(self.languages.values())

        for root_template in self.SOURCE_ROOTS:
            en_dir = Path(root_template.format(lang="en"))
            if not en_dir.is_dir():
                continue

            for en_file in sorted(en_dir.glob("*strings.xml")):
                # skip loading empty files
                try:
                    en_root = ET.parse(en_file).getroot()
                except ET.ParseError:
                    continue
                if not en_root.findall("string"):
                    continue

                stem = en_file.stem

                # skip if already loaded from another root
                if stem in self.entry_list:
                    continue

                self.entry_list[stem] = {}

                # collect the list of string IDs from the English file
                en_string_ids = [el.get("id") for el in en_root.findall("string") if el.get("id")]

                # derive the format filename
                format_stem = stem.replace("strings", "format")

                for string_id in en_string_ids:
                    self.entry_list[stem][string_id] = {}

                    for lang_code in lang_codes:
                        lang_dir = Path(root_template.format(lang=lang_code))
                        xml_path = lang_dir / en_file.name

                        # relative path stored on the entry so export_entries can write it
                        rel_path = xml_path.relative_to(Path("../DreamWorld_data"))

                        str_data = self._parse_strings_xml(xml_path) if xml_path.exists() else {}
                        row = str_data.get(string_id, {})
                        entry = StringEntry(
                            string_id=string_id,
                            text_string=row.get("string", ""),
                            is_translated=row.get("is_translation", False),
                            path=str(rel_path)
                        )

                        # apply formatting from the companion _format file
                        fmt_path = lang_dir / (format_stem + en_file.suffix)
                        if fmt_path.exists():
                            fmt_data = self._parse_format_xml(fmt_path)
                            for field, value in fmt_data.get(string_id, {}).items():
                                setattr(entry, field, value)

                        self.entry_list[stem][string_id][lang_code] = entry

    def _refresh_widgets(self) -> None:
        file = self.sel_file.currentText()
        sel_lang = self.languages[self.sel_language.currentText()]
        ref_lang = self.languages[self.sel_ref_language.currentText()]
        show_comparison = sel_lang != ref_lang

        entries = list(self.entry_list[file].values())

        # update existing widgets or add new ones
        for i, lang_entries in enumerate(entries):
            entry = lang_entries[sel_lang]
            comparison_text = lang_entries[ref_lang].text_string if show_comparison else ""

            # if a widget already exists at this index, load the new data
            if i < self.layout.count():
                widget = self.layout.itemAt(i).widget()
                widget.has_comparison_str = show_comparison
                widget.comparison_text = comparison_text
                widget.load(entry)
            else:
                # else create a new one
                widget = XMLLineEditWidget(entry, comparison_text if show_comparison else None)
                self.layout.addWidget(widget)

        # remove any excess widgets if the new file has fewer strings
        while self.layout.count() > len(entries):
            item = self.layout.takeAt(self.layout.count() - 1)
            if item.widget():
                item.widget().deleteLater()

    def _add_widgets(self) -> None:
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

    def _clear_widgets(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def export_entries(self) -> None:
        BASE_PATH = Path("../DreamWorld_data")

        # group entries by their *_strings.xml path
        entries_by_strings_path: dict[str, list[StringEntry]] = {}

        all_entries = (
            entry
            for file_dict in self.entry_list.values()
            for id_dict in file_dict.values()
            for entry in id_dict.values()
        )

        for entry in all_entries:
            if not entry.path:
                continue
            strings_path = entry.path.replace("format.xml", "strings.xml")
            entries_by_strings_path.setdefault(strings_path, []).append(entry)

        for rel_strings_path, entries in entries_by_strings_path.items():
            strings_output_path = BASE_PATH / rel_strings_path
            strings_output_path.parent.mkdir(parents=True, exist_ok=True)

            format_output_path = strings_output_path.with_name(
                strings_output_path.name.replace("strings.xml", "format.xml")
            )

            lang_code = Path(rel_strings_path).parts[-3]
            locale = lang_code

            # -----------
            # STRINGS XML
            # -----------

            strings_root = ET.Element("data", locale=locale)

            for entry in entries:
                el = ET.SubElement(strings_root, "string", id=entry.string_id)

                if entry.is_translated:
                    el.set("unofficial", "true")

                # fall back to string_id if text is empty
                el.text = entry.text_string or entry.string_id

            ET.indent(strings_root, space="\t")

            with strings_output_path.open("w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="utf-8" ?>\n')
                f.write(ET.tostring(strings_root, encoding="unicode"))

            # ----------
            # FORMAT XML
            # ----------

            format_root = ET.Element("data", locale=locale)

            for entry in entries:
                attrs = {}

                if entry.size != self.default_entry.size:
                    attrs["size"] = str(entry.size)

                if entry.letterSpacing != self.default_entry.letterSpacing:
                    attrs["letterSpacing"] = str(entry.letterSpacing)

                if entry.leading != self.default_entry.leading:
                    attrs["leading"] = str(entry.leading)

                if entry.color != self.default_entry.color:
                    attrs["color"] = self._fix_color_str(entry.color)

                if entry.bold != self.default_entry.bold:
                    attrs["bold"] = "true"

                # skip empty format entries
                if not attrs:
                    continue

                el = ET.SubElement(format_root, "string", id=entry.string_id)

                for key, value in attrs.items():
                    el.set(key, value)

            ET.indent(format_root, space="\t")

            with format_output_path.open("w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="utf-8" ?>\n')
                f.write(
                    ET.tostring(
                        format_root,
                        encoding="unicode",
                        short_empty_elements=True
                    )
                )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()