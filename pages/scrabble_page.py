# Malayalam Games — Scrabble Mode Page
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class ScrabblePage(QWidget):
    """Malayalam tile-rack word game sharing vocabulary with Word Match."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window

        self.rack_index = 0
        self.tiles: list[str] = []
        self.bonus_index: int | None = None
        self.selected_indices: list[int] = []
        self.found_words: list[str] = []

        self._build_ui()

    def _build_ui(self):
        ml_font = self.window.ml_font_family
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header_lbl = QLabel("🎲 Scrabble — Malayalam Tile Rack")
        header_lbl.setAlignment(Qt.AlignCenter)
        header_lbl.setFont(QFont(ml_font, 20, QFont.Bold))
        header_lbl.setStyleSheet("color: #1B4332;")

        self.word_lbl = QLabel("")
        self.word_lbl.setAlignment(Qt.AlignCenter)
        self.word_lbl.setFont(QFont(ml_font, 28, QFont.Bold))
        self.word_lbl.setStyleSheet(
            "background: #FFFFFF; color: #1B4332; border: 2px solid #95D5B2; "
            "border-radius: 16px; padding: 12px;"
        )

        rack_row = QHBoxLayout()
        rack_row.addStretch(1)
        self.tile_buttons: list[QPushButton] = []
        for i in range(8):
            btn = QPushButton()
            btn.setFont(QFont(ml_font, 20, QFont.Bold))
            btn.setFixedSize(86, 78)
            btn.setStyleSheet(
                "QPushButton { background: #FFFDF7; color: #1B4332; border: 2px solid #2D6A4F; "
                "border-radius: 14px; } "
                "QPushButton:hover:enabled { background: #E8F8F0; } "
                "QPushButton:disabled { background: #E9ECEF; color: #ADB5BD; border-color: #DEE2E6; }"
            )
            btn.clicked.connect(lambda checked=False, idx=i: self._on_tile_clicked(idx))
            rack_row.addWidget(btn)
            self.tile_buttons.append(btn)
        rack_row.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        back_btn = QPushButton("⌫ Undo")
        back_btn.setObjectName("ActionBtn")
        back_btn.clicked.connect(self._backspace_word)

        clear_btn = QPushButton("🧹 Clear")
        clear_btn.setObjectName("ActionBtn")
        clear_btn.clicked.connect(self._clear_word)

        shuffle_btn = QPushButton("🔀 Shuffle")
        shuffle_btn.setObjectName("ActionBtn")
        shuffle_btn.clicked.connect(self._shuffle_rack)

        submit_btn = QPushButton("✅ Submit Word")
        submit_btn.setObjectName("ActionBtn")
        submit_btn.setStyleSheet(
            "background-color: #2D6A4F; color: #FFFFFF; border-radius: 14px; "
            "padding: 10px 20px; font-size: 14px; font-weight: bold;"
        )
        submit_btn.clicked.connect(self._submit_word)

        new_rack_btn = QPushButton("🆕 New Rack")
        new_rack_btn.setObjectName("ActionBtn")
        new_rack_btn.clicked.connect(self._new_rack)

        for b in (back_btn, clear_btn, shuffle_btn, submit_btn, new_rack_btn):
            btn_row.addWidget(b)
        btn_row.addStretch(1)

        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setAlignment(Qt.AlignCenter)
        self.feedback_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #2D6A4F;")

        self.found_lbl = QLabel("")
        self.found_lbl.setAlignment(Qt.AlignCenter)
        self.found_lbl.setFont(QFont(ml_font, 16, QFont.Bold))
        self.found_lbl.setStyleSheet(
            "background: #FFFFFF; color: #1B4332; border: 1px solid #D8F3DC; "
            "border-radius: 12px; padding: 10px;"
        )

        layout.addWidget(header_lbl)
        layout.addWidget(self.word_lbl)
        layout.addLayout(rack_row)
        layout.addLayout(btn_row)
        layout.addWidget(self.feedback_lbl)
        layout.addWidget(self.found_lbl)
        layout.addStretch()

    def _word_lookup(self) -> dict[str, dict[str, str]]:
        lookup: dict[str, dict[str, str]] = {}
        for item in getattr(self.window, "vocab_items", []):
            ml = (item.get("ml") or "").strip()
            if len(ml) >= 2 and ml not in lookup:
                lookup[ml] = {
                    "id": item.get("id", ""),
                    "en": item.get("en", ""),
                }
        return lookup

    def _score_selection(self, indices: list[int]) -> int:
        total = 0
        hit_bonus = False
        for idx in indices:
            tile = self.tiles[idx]
            pts = 2 if len(tile) > 1 else 1
            if self.bonus_index is not None and idx == self.bonus_index:
                hit_bonus = True
            total += pts
        if hit_bonus:
            total *= 2
        if len(indices) >= 3:
            total += 2
        return total

    def on_racks_reloaded(self, reset_current_rack: bool = False):
        racks = getattr(self.window, "scrabble_racks", [])
        if racks:
            self.rack_index %= len(racks)
        else:
            self.rack_index = 0

        if reset_current_rack or not self.tiles:
            self.load_rack()
        else:
            self.refresh_ui()

    def load_rack(self):
        racks = getattr(self.window, "scrabble_racks", [])
        if not racks:
            self.tiles = []
            self.bonus_index = None
            self.selected_indices = []
            self.found_words = []
            self.refresh_ui()
            self.feedback_lbl.setText("No Scrabble racks found in scrabble_racks.csv.")
            self.feedback_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #D9534F;")
            return

        rack = racks[self.rack_index % len(racks)]
        self.tiles = list(rack["tiles"])
        self.bonus_index = rack.get("bonus_index")
        self.selected_indices = []
        self.found_words = []
        self.refresh_ui()
        self.feedback_lbl.setText(
            "Spell words from your Match vocabulary! 🌟 = 2x tile bonus"
        )
        self.feedback_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #2D6A4F;")

    def refresh_ui(self):
        formed = "".join(self.tiles[i] for i in self.selected_indices)
        self.word_lbl.setText(formed if formed else "Tap tiles to spell a Malayalam word...")

        for idx, btn in enumerate(self.tile_buttons):
            if idx < len(self.tiles):
                tile = self.tiles[idx]
                is_bonus = self.bonus_index is not None and idx == self.bonus_index
                btn.setText(f"{tile}\n{'🌟' if is_bonus else '·'}")
                btn.setVisible(True)
                btn.setEnabled(idx not in self.selected_indices)
            else:
                btn.setText("")
                btn.setVisible(False)

        if self.found_words:
            self.found_lbl.setText(
                f"Found ({len(self.found_words)}):  " + "   •   ".join(self.found_words)
            )
        else:
            self.found_lbl.setText("Found words this rack: None yet")

    def _on_tile_clicked(self, idx: int):
        if idx in self.selected_indices or idx < 0 or idx >= len(self.tiles):
            return
        self.selected_indices.append(idx)
        self.refresh_ui()

    def _backspace_word(self):
        if self.selected_indices:
            self.selected_indices.pop()
            self.refresh_ui()

    def _clear_word(self):
        self.selected_indices = []
        self.refresh_ui()

    def _shuffle_rack(self):
        if not self.tiles:
            return
        current_tiles = [
            (self.tiles[i], i == self.bonus_index)
            for i in range(len(self.tiles))
        ]
        random.shuffle(current_tiles)
        self.tiles = [t for t, _ in current_tiles]
        self.bonus_index = next((i for i, (_, b) in enumerate(current_tiles) if b), None)
        self.selected_indices = []
        self.refresh_ui()
        self.feedback_lbl.setText("Rack shuffled!")
        self.feedback_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #2D6A4F;")

    def _submit_word(self):
        if not self.selected_indices:
            self.feedback_lbl.setText("Tap tiles first to form a word.")
            self.feedback_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #D9534F;")
            return

        formed = "".join(self.tiles[i] for i in self.selected_indices)
        lookup = self._word_lookup()

        if formed in self.found_words:
            self.feedback_lbl.setText(f"Already found '{formed}' in this rack!")
            self.feedback_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #D9534F;")
            self.selected_indices = []
            self.refresh_ui()
            return

        if formed in lookup:
            meta = lookup[formed]
            pts = self._score_selection(self.selected_indices)
            stars_earned = max(1, (pts + 1) // 2)
            self.window.add_stars(stars_earned)
            self.found_words.append(formed)
            self.selected_indices = []
            self.refresh_ui()
            en_suffix = f" ({meta['en']})" if meta.get("en") else ""
            self.feedback_lbl.setText(
                f"🎉 Valid word '{formed}'{en_suffix}! +{pts} pts (+{stars_earned} ⭐)"
            )
            self.feedback_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B7A43;")
            audio_id = meta.get("id", "")
            if audio_id:
                self.window.play_audio(audio_id)
        else:
            self.feedback_lbl.setText(
                f"'{formed}' is not in the Match vocabulary list yet — try another combination!"
            )
            self.feedback_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #D9534F;")

    def _new_rack(self):
        racks = getattr(self.window, "scrabble_racks", [])
        if racks:
            self.rack_index = (self.rack_index + 1) % len(racks)
            self.load_rack()