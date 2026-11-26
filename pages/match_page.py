# Malayalam Games — Word Match Mode Page
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import random

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui_styles import make_translucent_widget, style_frosted_panel


class MatchPage(QWidget):
    """Picture-and-word matching page with category filtering and hover reveal."""

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

    WORD_CARD_STYLE = """
        QPushButton#WordCard {
            background-color: rgba(255, 255, 255, 242);
            color: #1B4332;
            border: 2px solid #B7E4C7;
            border-radius: 16px;
        }
        QPushButton#WordCard:hover {
            background-color: #F4FBF7;
            border-color: #40916C;
        }
        QPushButton#WordCard:pressed {
            background-color: #E8F8F0;
            border-color: #1B4332;
        }
    """

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.selected_category = "All"
        self.current_target = None
        self.current_choices: list[dict] = []
        self._prompt_hovered = False
        self.cat_buttons: dict[str, QPushButton] = {}

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

        banner = QFrame()
        style_frosted_panel(banner, object_name="MatchBanner", alpha=125, radius=18)
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(20, 12, 20, 12)

        self.prompt_lbl = QLabel("Find: ...")
        self.prompt_lbl.setFont(QFont(ml_font, 24, QFont.Bold))
        self.prompt_lbl.setStyleSheet("color: #1B4332; background: transparent; border: none;")
        self.prompt_lbl.setAttribute(Qt.WA_Hover, True)
        self.prompt_lbl.installEventFilter(self)

        hear_btn = QPushButton("🔊 Hear Word")
        hear_btn.setObjectName("ActionBtn")
        hear_btn.setMinimumSize(170, 44)
        hear_btn.setStyleSheet("""
            QPushButton#ActionBtn {
                background-color: #FF8C42;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 10px 18px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#ActionBtn:hover {
                background-color: #F27424;
                color: #FFFFFF;
            }
        """)
        hear_btn.clicked.connect(
            lambda: self.window.play_audio(self.current_target["id"]) if self.current_target else None
        )

        banner_layout.addWidget(self.prompt_lbl)
        banner_layout.addStretch()
        banner_layout.addWidget(hear_btn)
        layout.addWidget(banner)

        grid_wrapper = QHBoxLayout()
        grid_wrapper.addStretch(1)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        self.card_buttons: list[QPushButton] = []
        self.card_widgets: list[tuple[QLabel, QLabel, QLabel]] = []

        for idx in range(4):
            btn = QPushButton()
            btn.setObjectName("WordCard")
            btn.setFixedSize(360, 160)
            btn.setStyleSheet(self.WORD_CARD_STYLE)
            btn.clicked.connect(lambda checked=False, i=idx: self.check_answer(i))

            card_layout = QVBoxLayout(btn)
            card_layout.setContentsMargins(14, 10, 14, 10)
            card_layout.setSpacing(4)
            card_layout.setAlignment(Qt.AlignCenter)

            emoji_lbl = QLabel()
            emoji_lbl.setAlignment(Qt.AlignCenter)
            emoji_lbl.setStyleSheet("font-size: 30px; background: transparent; border: none;")
            emoji_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

            ml_lbl = QLabel()
            ml_lbl.setAlignment(Qt.AlignCenter)
            ml_lbl.setFont(QFont(ml_font, 28, QFont.Bold))
            ml_lbl.setStyleSheet("color: #1B4332; background: transparent; border: none;")
            ml_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

            en_lbl = QLabel()
            en_lbl.setAlignment(Qt.AlignCenter)
            en_lbl.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #2D6A4F; "
                "background: transparent; border: none;"
            )
            en_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

            card_layout.addWidget(emoji_lbl)
            card_layout.addWidget(ml_lbl)
            card_layout.addWidget(en_lbl)

            grid.addWidget(btn, idx // 2, idx % 2)
            self.card_buttons.append(btn)
            self.card_widgets.append((emoji_lbl, ml_lbl, en_lbl))

        grid_wrapper.addLayout(grid)
        grid_wrapper.addStretch(1)
        layout.addLayout(grid_wrapper)

        self.feedback_lbl = QLabel("Tap the matching picture card!")
        self.feedback_lbl.setAlignment(Qt.AlignCenter)
        self.feedback_lbl.setAttribute(Qt.WA_TranslucentBackground, True)
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )
        layout.addWidget(self.feedback_lbl)

    def eventFilter(self, obj, event):
        if obj is self.prompt_lbl:
            if event.type() == QEvent.Enter:
                self._prompt_hovered = True
                self._update_prompt_display(True)
            elif event.type() == QEvent.Leave:
                self._prompt_hovered = False
                self._update_prompt_display(False)
        return super().eventFilter(obj, event)

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

    def _update_prompt_display(self, revealed: bool):
        if not self.current_target:
            self.prompt_lbl.setText("Find: ...")
            return
        en = self.current_target["en"]
        ml = self.current_target["ml"]
        if revealed:
            self.prompt_lbl.setText(f"Find:  {ml}   ({en})")
        else:
            self.prompt_lbl.setText(f"Find:  ••••••   ({en})")

    def next_round(self):
        items = self._vocab_items()
        pool = (
            items
            if self.selected_category == "All"
            else [w for w in items if w["cat"] == self.selected_category]
        )
        if not pool:
            return
        choices = random.sample(pool, min(4, len(pool)))
        self.current_target = random.choice(choices)
        self.current_choices = choices

        self._update_prompt_display(self._prompt_hovered)
        self.feedback_lbl.setText("Tap the matching card!")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )

        for idx, ((emoji_lbl, ml_lbl, en_lbl), btn) in enumerate(zip(self.card_widgets, self.card_buttons)):
            if idx < len(choices):
                item = choices[idx]
                emoji_lbl.setText(item["emoji"])
                ml_lbl.setText(item["ml"])
                en_lbl.setText(item["en"])
                btn.setEnabled(True)
            else:
                emoji_lbl.setText("")
                ml_lbl.setText("")
                en_lbl.setText("")
                btn.setEnabled(False)

        self.window.play_audio(self.current_target["id"])

    def check_answer(self, idx: int):
        if idx >= len(self.current_choices) or not self.current_target:
            return
        chosen = self.current_choices[idx]
        if chosen["id"] == self.current_target["id"]:
            self.window.add_stars(1)
            self.feedback_lbl.setText(f"🎉 ശരിയാണ്! (Correct!)  {chosen['ml']} = {chosen['en']}")
            self.feedback_lbl.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #1B7A43; background: transparent;"
            )
            self.next_round()
        else:
            self.feedback_lbl.setText(f"Try again! That was {chosen['ml']} ({chosen['en']}).")
            self.feedback_lbl.setStyleSheet(
                "font-size: 17px; font-weight: bold; color: #D9534F; background: transparent;"
            )
            self.window.play_audio(
                chosen["id"],
                followup_phrase=("Try again", "en-US-AriaNeural"),
            )

    def show_reloaded_feedback(self):
        self.feedback_lbl.setText("🔄 Reloaded CSV data.")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )