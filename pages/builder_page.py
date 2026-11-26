# Malayalam Games — Word Builder Mode Page (വാക്കുകൾ കണ്ടെത്താമോ)
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui_styles import FROST_CARD_STYLE, make_translucent_widget, style_frosted_panel


def _split_malayalam_units(word: str) -> list[str]:
    """Split a Malayalam word into base characters plus attached diacritics/conjuncts."""
    combining_marks = {
        "\u0d00", "\u0d01", "\u0d02", "\u0d03",
        "\u0d3b", "\u0d3c",
        "\u0d3e", "\u0d3f", "\u0d40", "\u0d41", "\u0d42", "\u0d43", "\u0d44",
        "\u0d46", "\u0d47", "\u0d48", "\u0d4a", "\u0d4b", "\u0d4c", "\u0d4d",
        "\u0d57",
    }
    virama = "\u0d4d"
    units: list[str] = []
    i = 0
    while i < len(word):
        ch = word[i]
        if ch.isspace():
            i += 1
            continue
        unit = ch
        i += 1
        while i < len(word):
            nxt = word[i]
            if nxt in combining_marks:
                unit += nxt
                i += 1
                if nxt == virama and i < len(word) and not word[i].isspace():
                    unit += word[i]
                    i += 1
            else:
                break
        units.append(unit)
    return units


class BuilderPage(QWidget):
    """Malayalam word-builder page (വാക്കുകൾ കണ്ടെത്താമോ) with frosted cards over star backdrop."""

    CAT_SELECTED_STYLE = """
        QPushButton {
            background-color: #E8F8F0;
            color: #1B4332;
            border: 2px solid #1B4332;
            border-radius: 12px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: bold;
        }
    """

    CAT_UNSELECTED_STYLE = """
        QPushButton {
            background-color: rgba(255, 255, 255, 240);
            color: #2D6A4F;
            border: 2px solid #95D5B2;
            border-radius: 12px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #F4FBF7;
            color: #1B4332;
            border-color: #40916C;
        }
    """

    BUILDER_SLOT_EMPTY_STYLE = """
        QPushButton#BuilderSlot {
            background-color: rgba(255, 255, 255, 125);
            color: #2D6A4F;
            border: 2px dashed rgba(64, 145, 108, 195);
            border-radius: 14px;
            min-width: 66px;
            min-height: 68px;
        }
        QPushButton#BuilderSlot:hover {
            background-color: rgba(244, 251, 247, 195);
            border-color: #1B4332;
        }
    """

    BUILDER_SLOT_FILLED_STYLE = """
        QPushButton#BuilderSlot {
            background-color: rgba(255, 255, 255, 242);
            color: #1B4332;
            border: 2px solid #2D6A4F;
            border-radius: 14px;
            min-width: 66px;
            min-height: 68px;
        }
        QPushButton#BuilderSlot:hover {
            background-color: #FFF3E6;
            border-color: #FF8C42;
        }
    """

    POOL_TILE_STYLE = (
        FROST_CARD_STYLE
        + """
        QPushButton#BuilderTile {
            background-color: rgba(255, 255, 255, 242);
            color: #1B4332;
            border: 2px solid #95D5B2;
            border-radius: 14px;
            min-width: 68px;
            min-height: 70px;
        }
        QPushButton#BuilderTile:hover {
            background-color: #E8F8F0;
            border-color: #40916C;
        }
        QPushButton#BuilderTile:pressed {
            background-color: #D8F3DC;
            border-color: #1B4332;
        }
        QPushButton#BuilderTile:disabled {
            background-color: rgba(255, 255, 255, 90);
            color: rgba(27, 67, 50, 80);
            border: 2px dashed rgba(149, 213, 178, 120);
        }
        """
    )

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.selected_category = "All"
        self.cat_buttons: dict[str, QPushButton] = {}
        self.puzzle_index = 0

        self.current_target: dict | None = None
        self.target_units: list[str] = []
        self.pool_units: list[str] = []
        self.pool_used: list[bool] = []
        self.slot_to_pool: list[int | None] = []
        self.built_words: list[str] = []

        self.slot_buttons: list[QPushButton] = []
        self.pool_buttons: list[QPushButton] = []

        make_translucent_widget(self)
        self._build_ui()

    def _vocab_items(self) -> list[dict]:
        return getattr(self.window, "vocab_items", [])

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def _style_cat_button(self, btn: QPushButton, is_selected: bool):
        btn.setChecked(is_selected)
        btn.setStyleSheet(self.CAT_SELECTED_STYLE if is_selected else self.CAT_UNSELECTED_STYLE)
        btn.update()

    def _build_ui(self):
        ml_font = self.window.ml_font_family
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 6)
        layout.setSpacing(8)

        # Category filter bar
        cat_row = QHBoxLayout()
        cat_row.setSpacing(6)

        arrow_style = """
            QPushButton#CatArrow {
                background-color: rgba(255, 255, 255, 240);
                color: #1B4332;
                border: 2px solid #95D5B2;
                border-radius: 12px;
                padding: 0px;
                font-size: 14px;
                font-weight: bold;
                min-width: 34px;
                max-width: 34px;
                min-height: 36px;
                max-height: 36px;
            }
            QPushButton#CatArrow:hover:enabled {
                background-color: #E8F8F0;
                color: #1B4332;
                border-color: #40916C;
            }
            QPushButton#CatArrow:pressed:enabled {
                background-color: #D8F3DC;
                color: #1B4332;
                border-color: #2D6A4F;
            }
            QPushButton#CatArrow:disabled {
                background-color: rgba(234, 242, 238, 190);
                color: #7A9E8B;
                border-color: #C7DFD2;
            }
        """

        self.cat_left_btn = QPushButton("◀")
        self.cat_left_btn.setObjectName("CatArrow")
        self.cat_left_btn.setFocusPolicy(Qt.NoFocus)
        self.cat_left_btn.setStyleSheet(arrow_style)
        self.cat_left_btn.clicked.connect(lambda: self._scroll_categories(-180))

        self.cat_scroll = QScrollArea()
        self.cat_scroll.setWidgetResizable(True)
        self.cat_scroll.setFixedHeight(42)
        self.cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cat_scroll.setFrameShape(QFrame.NoFrame)
        make_translucent_widget(self.cat_scroll)

        self.cat_container = QWidget()
        make_translucent_widget(self.cat_container)
        self.cat_bar = QHBoxLayout(self.cat_container)
        self.cat_bar.setContentsMargins(0, 2, 0, 2)
        self.cat_bar.setSpacing(8)
        self.cat_scroll.setWidget(self.cat_container)

        self.cat_right_btn = QPushButton("▶")
        self.cat_right_btn.setObjectName("CatArrow")
        self.cat_right_btn.setFocusPolicy(Qt.NoFocus)
        self.cat_right_btn.setStyleSheet(arrow_style)
        self.cat_right_btn.clicked.connect(lambda: self._scroll_categories(180))

        hbar = self.cat_scroll.horizontalScrollBar()
        hbar.valueChanged.connect(self._update_cat_arrows)
        hbar.rangeChanged.connect(self._update_cat_arrows)

        cat_row.addWidget(self.cat_left_btn)
        cat_row.addWidget(self.cat_scroll, stretch=1)
        cat_row.addWidget(self.cat_right_btn)
        layout.addLayout(cat_row)

        # Frosted prompt & action banner
        banner = QFrame()
        style_frosted_panel(banner, object_name="BuilderBanner", alpha=125, radius=18)
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(20, 12, 20, 12)

        self.prompt_lbl = QLabel("വാക്കുകൾ കണ്ടെത്താമോ  •  Build: ...")
        self.prompt_lbl.setFont(QFont(ml_font, 21, QFont.Bold))
        self.prompt_lbl.setStyleSheet("color: #1B4332; background: transparent; border: none;")

        hear_btn = QPushButton("🔊 Hear Word")
        hear_btn.setObjectName("ActionBtn")
        hear_btn.setMinimumSize(155, 42)
        hear_btn.setStyleSheet("""
            QPushButton#ActionBtn {
                background-color: #FF8C42;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#ActionBtn:hover {
                background-color: #F27424;
                color: #FFFFFF;
            }
        """)
        hear_btn.clicked.connect(
            lambda: self.window.play_audio(self.current_target["id"])
            if self.current_target and self.current_target.get("id")
            else None
        )

        reset_btn = QPushButton("↩ Clear")
        reset_btn.setObjectName("ClearBtn")
        reset_btn.setMinimumSize(105, 42)
        reset_btn.setStyleSheet("""
            QPushButton#ClearBtn {
                background-color: rgba(255, 255, 255, 225);
                color: #1B4332;
                border: 2px solid #95D5B2;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#ClearBtn:hover {
                background-color: #E8F8F0;
                border-color: #40916C;
            }
        """)
        reset_btn.clicked.connect(self.clear_word)

        skip_btn = QPushButton("Next Word ▶")
        skip_btn.setObjectName("NextBtn")
        skip_btn.setMinimumSize(120, 42)
        skip_btn.setStyleSheet("""
            QPushButton#NextBtn {
                background-color: rgba(232, 248, 240, 235);
                color: #1B4332;
                border: 2px solid #40916C;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#NextBtn:hover {
                background-color: #D8F3DC;
                border-color: #1B4332;
            }
        """)
        skip_btn.clicked.connect(self.next_round)

        banner_layout.addWidget(self.prompt_lbl)
        banner_layout.addStretch()
        banner_layout.addWidget(hear_btn)
        banner_layout.addWidget(reset_btn)
        banner_layout.addWidget(skip_btn)
        layout.addWidget(banner)

        # Target slots strip (transparent over star backdrop)
        slots_wrap = QWidget()
        make_translucent_widget(slots_wrap)
        self.slots_layout = QHBoxLayout(slots_wrap)
        self.slots_layout.setContentsMargins(8, 8, 8, 8)
        self.slots_layout.setSpacing(10)
        self.slots_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(slots_wrap)

        # Syllable/letter tile pool strip (transparent over star backdrop)
        pool_wrap = QWidget()
        make_translucent_widget(pool_wrap)
        self.pool_layout = QHBoxLayout(pool_wrap)
        self.pool_layout.setContentsMargins(8, 8, 8, 8)
        self.pool_layout.setSpacing(10)
        self.pool_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(pool_wrap)

        # Frosted "Completed Words" shelf
        self.built_panel = QFrame()
        style_frosted_panel(self.built_panel, object_name="BuiltShelf", alpha=115, radius=16)
        built_layout = QHBoxLayout(self.built_panel)
        built_layout.setContentsMargins(16, 10, 16, 10)
        built_layout.setSpacing(10)

        self.built_lbl = QLabel("Completed Words: —")
        self.built_lbl.setFont(QFont(ml_font, 15, QFont.Bold))
        self.built_lbl.setStyleSheet("color: #1B4332; background: transparent; border: none;")
        self.built_lbl.setWordWrap(True)
        built_layout.addWidget(self.built_lbl)
        layout.addWidget(self.built_panel)

        layout.addStretch(1)

        # Feedback line
        self.feedback_lbl = QLabel("Tap Malayalam tiles to build the word!")
        self.feedback_lbl.setAlignment(Qt.AlignCenter)
        self.feedback_lbl.setAttribute(Qt.WA_TranslucentBackground, True)
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )
        layout.addWidget(self.feedback_lbl)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._update_cat_arrows)

    def _scroll_categories(self, delta_px: int):
        hbar = self.cat_scroll.horizontalScrollBar()
        hbar.setValue(hbar.value() + delta_px)
        self._update_cat_arrows()

    def _update_cat_arrows(self, *_):
        hbar = self.cat_scroll.horizontalScrollBar()
        has_overflow = hbar.maximum() > hbar.minimum()
        self.cat_left_btn.setVisible(has_overflow)
        self.cat_right_btn.setVisible(has_overflow)
        self.cat_left_btn.setEnabled(hbar.value() > hbar.minimum())
        self.cat_right_btn.setEnabled(hbar.value() < hbar.maximum())

    def rebuild_categories(self):
        self._clear_layout(self.cat_bar)
        self.cat_buttons = {}
        categories = ["All"] + list(dict.fromkeys(item["cat"] for item in self._vocab_items()))
        if self.selected_category not in categories:
            self.selected_category = "All"

        for cat in categories:
            btn = QPushButton(cat.replace("&", "&&"))
            btn.setObjectName("CatBtn")
            btn.setCheckable(True)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked, c=cat: self.set_category(c))
            self._style_cat_button(btn, cat == self.selected_category)
            self.cat_bar.addWidget(btn)
            self.cat_buttons[cat] = btn
        self.cat_bar.addStretch()
        QTimer.singleShot(0, self._update_cat_arrows)

    def set_category(self, category: str):
        self.selected_category = category
        for cat, btn in self.cat_buttons.items():
            self._style_cat_button(btn, cat == category)
        self.next_round()

    def _update_built_label(self):
        if not self.built_words:
            self.built_lbl.setText("Completed Words: —")
        else:
            joined = "   •   ".join(self.built_words)
            self.built_lbl.setText(f"Completed Words ({len(self.built_words)}):  {joined}")

    def _setup_target_item(self, item: dict, source_pool: list[dict]):
        ml = item.get("ml") or item.get("word") or ""
        en = item.get("en") or item.get("hint") or item.get("meaning") or ""
        emoji = item.get("emoji", "")
        units = _split_malayalam_units(ml)
        if not units:
            return False

        self.current_target = {
            "id": item.get("id", ""),
            "ml": ml,
            "en": en,
            "emoji": emoji,
        }
        self.target_units = units

        distractors: list[str] = []
        other_words = [w for w in source_pool if w.get("id") != item.get("id")]
        random.shuffle(other_words)
        for other in other_words:
            for u in _split_malayalam_units(other.get("ml") or other.get("word") or ""):
                if u not in self.target_units and u not in distractors:
                    distractors.append(u)
                if len(distractors) >= 2:
                    break
            if len(distractors) >= 2:
                break

        self.pool_units = self.target_units + distractors
        random.shuffle(self.pool_units)
        self.pool_used = [False] * len(self.pool_units)
        self.slot_to_pool = [None] * len(self.target_units)

        self.prompt_lbl.setText(f"വാക്കുകൾ കണ്ടെത്താമോ  •  {emoji}  {en}".strip())
        self.feedback_lbl.setText("Tap tiles from below to fill each slot!")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )

        self._rebuild_board()
        if self.current_target.get("id"):
            self.window.play_audio(self.current_target["id"])
        return True

    def load_puzzle(self):
        """Load puzzle from word_puzzles if available, otherwise fall back to vocab_items."""
        puzzles = getattr(self.window, "word_puzzles", [])
        if puzzles:
            idx = self.puzzle_index % len(puzzles)
            if self._setup_target_item(puzzles[idx], puzzles):
                return
        self.next_round()

    def on_puzzles_reloaded(self):
        self.puzzle_index = 0
        self.load_puzzle()

    def next_round(self):
        items = self._vocab_items()
        pool = (
            items
            if self.selected_category == "All"
            else [w for w in items if w.get("cat") == self.selected_category]
        )
        valid_pool = [w for w in pool if len(_split_malayalam_units(w.get("ml", ""))) >= 1]
        if not valid_pool:
            return

        chosen = random.choice(valid_pool)
        self._setup_target_item(chosen, valid_pool)

    def _rebuild_board(self):
        self._clear_layout(self.slots_layout)
        self._clear_layout(self.pool_layout)
        self.slot_buttons = []
        self.pool_buttons = []

        ml_font = self.window.ml_font_family

        for s_idx in range(len(self.slot_to_pool)):
            slot_btn = QPushButton("")
            slot_btn.setObjectName("BuilderSlot")
            slot_btn.setFont(QFont(ml_font, 26, QFont.Bold))
            slot_btn.clicked.connect(lambda checked=False, i=s_idx: self._on_slot_clicked(i))
            self.slots_layout.addWidget(slot_btn)
            self.slot_buttons.append(slot_btn)

        for p_idx, unit in enumerate(self.pool_units):
            tile_btn = QPushButton(unit)
            tile_btn.setObjectName("BuilderTile")
            tile_btn.setFont(QFont(ml_font, 26, QFont.Bold))
            tile_btn.clicked.connect(lambda checked=False, i=p_idx: self._on_pool_clicked(i))
            self.pool_layout.addWidget(tile_btn)
            self.pool_buttons.append(tile_btn)

        self._refresh_visuals()

    def _on_pool_clicked(self, pool_idx: int):
        if pool_idx < 0 or pool_idx >= len(self.pool_units) or self.pool_used[pool_idx]:
            return
        empty_slot = next((i for i, p in enumerate(self.slot_to_pool) if p is None), None)
        if empty_slot is None:
            return

        self.slot_to_pool[empty_slot] = pool_idx
        self.pool_used[pool_idx] = True
        self._refresh_visuals()
        self._evaluate_word()

    def _on_slot_clicked(self, slot_idx: int):
        if slot_idx < 0 or slot_idx >= len(self.slot_to_pool):
            return
        pool_idx = self.slot_to_pool[slot_idx]
        if pool_idx is None:
            return

        self.slot_to_pool[slot_idx] = None
        self.pool_used[pool_idx] = False
        self._refresh_visuals()
        self.feedback_lbl.setText("Tap tiles from below to fill each slot!")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )

    def clear_word(self):
        self.slot_to_pool = [None] * len(self.target_units)
        self.pool_used = [False] * len(self.pool_units)
        self._refresh_visuals()
        self.feedback_lbl.setText("Cleared! Try building the word again.")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )

    def _refresh_visuals(self):
        for s_idx, btn in enumerate(self.slot_buttons):
            pool_idx = self.slot_to_pool[s_idx]
            if pool_idx is None:
                btn.setText("")
                btn.setStyleSheet(self.BUILDER_SLOT_EMPTY_STYLE)
            else:
                btn.setText(self.pool_units[pool_idx])
                btn.setStyleSheet(self.BUILDER_SLOT_FILLED_STYLE)

        for p_idx, btn in enumerate(self.pool_buttons):
            btn.setEnabled(not self.pool_used[p_idx])
            btn.setStyleSheet(self.POOL_TILE_STYLE)

    def _evaluate_word(self):
        if any(p is None for p in self.slot_to_pool) or not self.current_target:
            return

        assembled_units = [self.pool_units[p] for p in self.slot_to_pool if p is not None]
        if assembled_units == self.target_units:
            ml = self.current_target["ml"]
            en = self.current_target["en"]
            entry = f"{ml} ({en})"
            if entry not in self.built_words:
                self.built_words.append(entry)
                self._update_built_label()
            self.window.add_stars(1)
            self.feedback_lbl.setText(f"🎉 ശരിയാണ്! (Correct!)  {ml} = {en}")
            self.feedback_lbl.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #1B7A43; background: transparent;"
            )
            self.puzzle_index += 1
            QTimer.singleShot(900, self.load_puzzle)
        else:
            self.feedback_lbl.setText("Not quite! Tap a filled slot to swap or press Clear.")
            self.feedback_lbl.setStyleSheet(
                "font-size: 17px; font-weight: bold; color: #D9534F; background: transparent;"
            )

    def show_reloaded_feedback(self):
        self.feedback_lbl.setText("🔄 Reloaded CSV data.")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )


WordBuilderPage = BuilderPage