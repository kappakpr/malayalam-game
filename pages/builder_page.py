# Malayalam Games — Guided Word Builder Mode Page
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class BuilderPage(QWidget):
    """Guided Malayalam word assembly puzzle page."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window

        self.puzzle_index = 0
        self.current_puzzle = None
        self.current_tiles: list[str] = []
        self.selected_indices: list[int] = []

        self._build_ui()

    def _build_ui(self):
        ml_font = self.window.ml_font_family
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        self.clue_lbl = QLabel("Builder")
        self.clue_lbl.setAlignment(Qt.AlignCenter)
        self.clue_lbl.setFont(QFont(ml_font, 20, QFont.Bold))
        self.clue_lbl.setStyleSheet("color: #1B4332;")

        self.formed_word_lbl = QLabel("")
        self.formed_word_lbl.setAlignment(Qt.AlignCenter)
        self.formed_word_lbl.setFont(QFont(ml_font, 30, QFont.Bold))
        self.formed_word_lbl.setStyleSheet(
            "background: #FFFFFF; color: #1B4332; border: 2px solid #95D5B2; "
            "border-radius: 16px; padding: 14px;"
        )

        tiles_row = QHBoxLayout()
        tiles_row.addStretch(1)
        self.tile_buttons: list[QPushButton] = []
        for i in range(8):
            btn = QPushButton()
            btn.setFont(QFont(ml_font, 24, QFont.Bold))
            btn.setFixedSize(84, 74)
            btn.setStyleSheet(
                "QPushButton { background: #FFFFFF; color: #1B4332; border: 2px solid #40916C; "
                "border-radius: 14px; } "
                "QPushButton:disabled { background: #E9ECEF; color: #ADB5BD; border-color: #DEE2E6; }"
            )
            btn.clicked.connect(lambda checked=False, idx=i: self._on_tile_clicked(idx))
            tiles_row.addWidget(btn)
            self.tile_buttons.append(btn)
        tiles_row.addStretch(1)

        actions_row = QHBoxLayout()
        actions_row.addStretch(1)

        clear_btn = QPushButton("🧹 Clear")
        clear_btn.setObjectName("ActionBtn")
        clear_btn.clicked.connect(self.clear_selection)

        check_btn = QPushButton("✅ Check Word")
        check_btn.setObjectName("ActionBtn")
        check_btn.setStyleSheet(
            "background-color: #2D6A4F; color: #FFFFFF; border-radius: 14px; "
            "padding: 10px 20px; font-size: 15px; font-weight: bold;"
        )
        check_btn.clicked.connect(self.check_word)

        actions_row.addWidget(clear_btn)
        actions_row.addWidget(check_btn)
        actions_row.addStretch(1)

        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setAlignment(Qt.AlignCenter)
        self.feedback_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D6A4F;")

        layout.addWidget(self.clue_lbl)
        layout.addWidget(self.formed_word_lbl)
        layout.addLayout(tiles_row)
        layout.addLayout(actions_row)
        layout.addWidget(self.feedback_lbl)
        layout.addStretch()

    def _puzzles(self) -> list[dict]:
        return getattr(self.window, "word_puzzles", [])

    def on_puzzles_reloaded(self):
        puzzles = self._puzzles()
        if puzzles:
            self.puzzle_index %= len(puzzles)
        else:
            self.puzzle_index = 0
        if self.window.stack.currentWidget() is self:
            self.load_puzzle()
            self.feedback_lbl.setText("🔄 Reloaded word_builder.csv.")
            self.feedback_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D6A4F;")

    def load_puzzle(self):
        puzzles = self._puzzles()
        if not puzzles:
            self.current_puzzle = None
            self.current_tiles = []
            self.selected_indices = []
            self.clue_lbl.setText("No word puzzles available.")
            self.formed_word_lbl.setText("")
            for btn in self.tile_buttons:
                btn.setVisible(False)
            return

        puzzle = puzzles[self.puzzle_index % len(puzzles)]
        self.current_puzzle = puzzle
        tiles = puzzle.get("tiles") or puzzle.get("letters") or list(puzzle.get("word", ""))
        self.current_tiles = list(tiles)
        self.selected_indices = []
        self.refresh_ui()
        self.feedback_lbl.setText("Tap tiles below to form the word.")
        self.feedback_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D6A4F;")

    def refresh_ui(self):
        if not self.current_puzzle:
            return
        emoji = self.current_puzzle.get("emoji", "🧩")
        en = self.current_puzzle.get("en") or self.current_puzzle.get("meaning") or ""
        formed = "".join(self.current_tiles[i] for i in self.selected_indices)
        self.clue_lbl.setText(f"{emoji}  Builder — {en}".strip())
        self.formed_word_lbl.setText(formed if formed else "Tap letters below...")

        for idx, btn in enumerate(self.tile_buttons):
            if idx < len(self.current_tiles):
                btn.setText(self.current_tiles[idx])
                btn.setVisible(True)
                btn.setEnabled(idx not in self.selected_indices)
            else:
                btn.setText("")
                btn.setVisible(False)

    def _on_tile_clicked(self, tile_idx: int):
        if tile_idx in self.selected_indices or tile_idx < 0 or tile_idx >= len(self.current_tiles):
            return
        self.selected_indices.append(tile_idx)
        self.refresh_ui()

    def clear_selection(self):
        self.selected_indices = []
        self.refresh_ui()
        self.feedback_lbl.setText("Cleared. Tap tiles to build the word.")
        self.feedback_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D6A4F;")

    def check_word(self):
        if not self.current_puzzle:
            return
        formed = "".join(self.current_tiles[i] for i in self.selected_indices)
        target = self.current_puzzle.get("word") or self.current_puzzle.get("ml") or ""
        en = self.current_puzzle.get("en") or self.current_puzzle.get("meaning") or ""

        if formed and formed == target:
            self.window.add_stars(1)
            self.feedback_lbl.setText(
                f"🎉 ശരിയാണ്! {target}" + (f" ({en})" if en else "")
            )
            self.feedback_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #1B7A43;")
            if self.current_puzzle.get("id"):
                self.window.play_audio(self.current_puzzle["id"])
            puzzles = self._puzzles()
            if puzzles:
                self.puzzle_index = (self.puzzle_index + 1) % len(puzzles)
            QTimer.singleShot(900, self.load_puzzle)
        else:
            self.feedback_lbl.setText(f"Formed '{formed or '—'}' — try again!")
            self.feedback_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #D9534F;")