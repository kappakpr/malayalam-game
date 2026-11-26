# Malayalam Games — Letter Tracing Mode Page
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from tracing_canvas import TracingCanvas


class TracingPage(QWidget):
    """Interactive Malayalam character tracing screen."""

    PEN_COLORS = [
        ("🟠 Orange", "#E65100"),
        ("🔵 Blue", "#1565C0"),
        ("🟢 Green", "#2E7D32"),
        ("🟣 Purple", "#6A1B9A"),
        ("🩷 Pink", "#FFC0CB"),
    ]

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.letter_index = 0
        self._build_ui()

    def _build_ui(self):
        ml_font = self.window.ml_font_family
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.info_lbl = QLabel("Trace: അ")
        self.info_lbl.setFont(QFont(ml_font, 22, QFont.Bold))
        self.info_lbl.setStyleSheet("color: #1B4332;")

        say_letter_btn = QPushButton("🔊 Hear Letter")
        say_letter_btn.setMinimumSize(130, 44)
        say_letter_btn.setObjectName("ActionBtn")
        say_letter_btn.clicked.connect(self.play_current_letter)

        top_row.addWidget(self.info_lbl)
        top_row.addStretch()
        top_row.addWidget(say_letter_btn)
        layout.addLayout(top_row)

        self.canvas = TracingCanvas(ml_font, parent=self)
        layout.addWidget(self.canvas, stretch=1)

        controls = QHBoxLayout()
        self.color_group = QButtonGroup(self)
        self.color_group.setExclusive(True)

        first_color_btn = None
        for idx, (label, hex_code) in enumerate(self.PEN_COLORS):
            c_btn = QPushButton(label)
            c_btn.setCheckable(True)
            c_btn.setFocusPolicy(Qt.NoFocus)
            c_btn.setStyleSheet(
                f"QPushButton {{"
                f"  background: white; border: 2px solid {hex_code}; color: {hex_code};"
                f"  border-radius: 12px; padding: 8px 12px; font-weight: bold;"
                f"}}"
                f"QPushButton:checked {{"
                f"  background: {hex_code}; color: white; border: 3px solid #1B4332;"
                f"}}"
            )
            self.color_group.addButton(c_btn)
            c_btn.clicked.connect(lambda checked, col=hex_code: self.canvas.set_pen_color(col))
            controls.addWidget(c_btn)
            if idx == 0:
                first_color_btn = c_btn

        if first_color_btn is not None:
            first_color_btn.setChecked(True)

        controls.addStretch()

        clear_btn = QPushButton("🧹 Clear")
        clear_btn.setObjectName("ActionBtn")
        clear_btn.clicked.connect(self.canvas.clear_drawing)

        done_btn = QPushButton("⭐ Done / Next Letter →")
        done_btn.setObjectName("ActionBtn")
        done_btn.setStyleSheet(
            "background-color: #2D6A4F; color: white; border-radius: 14px; "
            "padding: 10px 20px; font-size: 15px; font-weight: bold;"
        )
        done_btn.clicked.connect(self.complete_letter)

        controls.addWidget(clear_btn)
        controls.addWidget(done_btn)
        layout.addLayout(controls)

    def _letters(self) -> list[dict]:
        return getattr(self.window, "trace_letters", [])

    def on_letters_reloaded(self):
        letters = self._letters()
        if letters:
            self.letter_index %= len(letters)
        else:
            self.letter_index = 0
        if self.window.stack.currentWidget() is self:
            self.load_letter()

    def load_letter(self):
        letters = self._letters()
        if not letters:
            self.info_lbl.setText("No tracing letters available.")
            self.canvas.set_character("")
            return
        letter_item = letters[self.letter_index % len(letters)]
        ml_char = letter_item.get("char") or letter_item.get("ml") or "?"
        label_text = letter_item.get("translit") or letter_item.get("name") or ""
        self.info_lbl.setText(
            f"Trace: {ml_char}  ({label_text})" if label_text else f"Trace: {ml_char}"
        )
        self.canvas.set_character(ml_char)
        if letter_item.get("id"):
            self.window.play_audio(letter_item["id"])

    def complete_letter(self):
        self.window.add_stars(1)
        letters = self._letters()
        if letters:
            self.letter_index = (self.letter_index + 1) % len(letters)
        self.load_letter()

    def play_current_letter(self):
        letters = self._letters()
        if not letters:
            return
        letter_item = letters[self.letter_index % len(letters)]
        if letter_item.get("id"):
            self.window.play_audio(letter_item["id"])