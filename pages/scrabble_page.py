# Malayalam Games — Scrabble Tile-Rack Mode Page
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


def _tokenize_malayalam(word: str) -> list[str]:
    """Split a Malayalam word into base characters plus attached diacritics/conjuncts."""
    combining_marks = {
        "\u0d00", "\u0d01", "\u0d02", "\u0d03",
        "\u0d3b", "\u0d3c",
        "\u0d3e", "\u0d3f", "\u0d40", "\u0d41", "\u0d42", "\u0d43", "\u0d44",
        "\u0d46", "\u0d47", "\u0d48", "\u0d4a", "\u0d4b", "\u0d4c", "\u0d4d",
        "\u0d57",
    }
    virama = "\u0d4d"
    tokens: list[str] = []
    i = 0
    while i < len(word):
        ch = word[i]
        if ch.isspace():
            i += 1
            continue
        token = ch
        i += 1
        while i < len(word):
            nxt = word[i]
            if nxt in combining_marks:
                token += nxt
                i += 1
                if nxt == virama and i < len(word) and not word[i].isspace():
                    token += word[i]
                    i += 1
            else:
                break
        tokens.append(token)
    return tokens


class ScrabblePage(QWidget):
    """Malayalam Scrabble mode: form valid words from a shared tray of letter tiles."""

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

    BOARD_TILE_STYLE = """
        QPushButton#BoardTile {
            background-color: rgba(255, 255, 255, 245);
            color: #1B4332;
            border: 2px solid #2D6A4F;
            border-radius: 14px;
            min-width: 66px;
            min-height: 70px;
        }
        QPushButton#BoardTile:hover {
            background-color: #FFF3E6;
            border-color: #FF8C42;
        }
    """

    RACK_TILE_STYLE = (
        FROST_CARD_STYLE
        + """
        QPushButton#RackTile {
            background-color: rgba(255, 249, 224, 245);
            color: #1B4332;
            border: 2px solid #E9B44C;
            border-radius: 14px;
            min-width: 68px;
            min-height: 72px;
        }
        QPushButton#RackTile:hover {
            background-color: #FFF3C4;
            border-color: #FF8C42;
        }
        QPushButton#RackTile:pressed {
            background-color: #FFE699;
            border-color: #1B4332;
        }
        QPushButton#RackTile:disabled {
            background-color: rgba(255, 255, 255, 85);
            color: rgba(27, 67, 50, 75);
            border: 2px dashed rgba(149, 213, 178, 120);
        }
        """
    )

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self.selected_category = "All"
        self.cat_buttons: dict[str, QPushButton] = {}
        self.rack_index = 0
        self.scrabble_points = 0

        self.tiles: list[str] = []
        self.rack_used: list[bool] = []
        self.active_rack_indices: list[int] = []
        self.scored_words: list[str] = []

        self.board_buttons: list[QPushButton] = []
        self.rack_buttons: list[QPushButton] = []

        make_translucent_widget(self)
        self._build_ui()

    def _vocab_items(self) -> list[dict]:
        return getattr(self.window, "vocab_items", [])

    def _word_lookup(self) -> dict[str, dict]:
        """Map Malayalam words to their vocabulary/puzzle metadata."""
        lookup: dict[str, dict] = {}
        for item in self._vocab_items():
            ml = (item.get("ml") or "").strip()
            if ml and ml not in lookup:
                lookup[ml] = item
        for puzzle in getattr(self.window, "word_puzzles", []):
            ml = (puzzle.get("ml") or puzzle.get("word") or "").strip()
            if ml and ml not in lookup:
                lookup[ml] = puzzle
        return lookup

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

        # Category filter strip
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

        # Frosted Scrabble action banner
        banner = QFrame()
        style_frosted_panel(banner, object_name="ScrabbleBanner", alpha=125, radius=18)
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(20, 10, 20, 10)
        banner_layout.setSpacing(10)

        self.rack_title_lbl = QLabel("🎲 Scrabble Rack  •  Form a Malayalam word!")
        self.rack_title_lbl.setFont(QFont(ml_font, 18, QFont.Bold))
        self.rack_title_lbl.setStyleSheet("color: #1B4332; background: transparent; border: none;")

        submit_btn = QPushButton("✅ Submit Word")
        submit_btn.setObjectName("ActionBtn")
        submit_btn.setMinimumHeight(40)
        submit_btn.setStyleSheet("""
            QPushButton#ActionBtn {
                background-color: #2D6A4F;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#ActionBtn:hover {
                background-color: #1B4332;
                color: #FFFFFF;
            }
        """)
        submit_btn.clicked.connect(self.submit_word)

        shuffle_btn = QPushButton("🔀 Shuffle")
        shuffle_btn.setMinimumHeight(40)
        shuffle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 230);
                color: #1B4332;
                border: 2px solid #95D5B2;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8F8F0;
                border-color: #40916C;
            }
        """)
        shuffle_btn.clicked.connect(self.shuffle_rack)

        clear_btn = QPushButton("↩ Clear")
        clear_btn.setMinimumHeight(40)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 230);
                color: #1B4332;
                border: 2px solid #95D5B2;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E8F8F0;
                border-color: #40916C;
            }
        """)
        clear_btn.clicked.connect(self.clear_board_tiles)

        new_rack_btn = QPushButton("🎲 New Rack")
        new_rack_btn.setMinimumHeight(40)
        new_rack_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8C42;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F27424;
                color: #FFFFFF;
            }
        """)
        new_rack_btn.clicked.connect(self.next_rack)

        banner_layout.addWidget(self.rack_title_lbl)
        banner_layout.addStretch()
        banner_layout.addWidget(submit_btn)
        banner_layout.addWidget(shuffle_btn)
        banner_layout.addWidget(clear_btn)
        banner_layout.addWidget(new_rack_btn)
        layout.addWidget(banner)

        # Active word staging strip (transparent over star backdrop)
        board_wrap = QWidget()
        make_translucent_widget(board_wrap)
        self.board_layout = QHBoxLayout(board_wrap)
        self.board_layout.setContentsMargins(8, 8, 8, 8)
        self.board_layout.setSpacing(10)
        self.board_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(board_wrap)

        # Scrabble tile tray (transparent over star backdrop)
        rack_wrap = QWidget()
        make_translucent_widget(rack_wrap)
        self.rack_layout = QHBoxLayout(rack_wrap)
        self.rack_layout.setContentsMargins(8, 8, 8, 8)
        self.rack_layout.setSpacing(10)
        self.rack_layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(rack_wrap)

        # Frosted scored words summary panel
        self.words_panel = QFrame()
        style_frosted_panel(self.words_panel, object_name="ScrabbleWordsPanel", alpha=115, radius=16)
        words_layout = QHBoxLayout(self.words_panel)
        words_layout.setContentsMargins(16, 10, 16, 10)
        self.words_lbl = QLabel("Words Made: —")
        self.words_lbl.setFont(QFont(ml_font, 15, QFont.Bold))
        self.words_lbl.setStyleSheet("color: #1B4332; background: transparent; border: none;")
        self.words_lbl.setWordWrap(True)
        words_layout.addWidget(self.words_lbl)
        layout.addWidget(self.words_panel)

        layout.addStretch(1)

        # Feedback line
        self.feedback_lbl = QLabel("Tap tiles from your rack to make a Malayalam word, then tap Submit Word!")
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
        self.load_rack()

    def _filtered_vocab(self) -> list[dict]:
        items = self._vocab_items()
        if self.selected_category == "All":
            return items
        return [w for w in items if w.get("cat") == self.selected_category]

    def _extract_rack_tiles(self, rack_obj: dict) -> list[str]:
        raw_tiles = rack_obj.get("tiles")
        if isinstance(raw_tiles, list) and raw_tiles:
            return [str(t).strip() for t in raw_tiles if str(t).strip()]
        if isinstance(raw_tiles, str) and raw_tiles.strip():
            sep = "|" if "|" in raw_tiles else ","
            return [t.strip() for t in raw_tiles.split(sep) if t.strip()]
        word = rack_obj.get("ml") or rack_obj.get("word") or ""
        return _tokenize_malayalam(word)

    def _build_combined_rack_from_vocab(self) -> list[str]:
        """Build a shared Scrabble tray of 7-8 Malayalam letter tiles from matching words."""
        pool = self._filtered_vocab() or self._vocab_items()
        if not pool:
            return []

        token_bag: list[str] = []
        sampled = random.sample(pool, min(3, len(pool)))
        for item in sampled:
            token_bag.extend(_tokenize_malayalam(item.get("ml", "")))

        random.shuffle(token_bag)
        tray = token_bag[:8]
        if len(tray) < 5:
            for item in pool:
                for tok in _tokenize_malayalam(item.get("ml", "")):
                    if len(tray) >= 6:
                        break
                    tray.append(tok)
                if len(tray) >= 6:
                    break
        random.shuffle(tray)
        return tray

    def load_rack(self):
        """Populate a Scrabble tile tray (distinct from single-word Builder clues)."""
        racks = getattr(self.window, "scrabble_racks", [])
        if racks:
            rack_obj = racks[self.rack_index % len(racks)]
            extracted = self._extract_rack_tiles(rack_obj)
            if extracted:
                self.tiles = extracted
            else:
                self.tiles = self._build_combined_rack_from_vocab()
        else:
            self.tiles = self._build_combined_rack_from_vocab()

        self.rack_used = [False] * len(self.tiles)
        self.active_rack_indices = []

        cat_label = "" if self.selected_category == "All" else f" [{self.selected_category}]"
        self.rack_title_lbl.setText(f"🎲 Scrabble{cat_label}  •  Pick tiles to form a word")
        self.feedback_lbl.setText("Tap rack tiles to build a Malayalam word, then press Submit Word.")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )
        self._rebuild_widgets()

    def next_rack(self):
        self.rack_index += 1
        self.load_rack()

    def refresh_ui(self):
        self._refresh_visuals()
        self._refresh_words_label()

    def on_racks_reloaded(self, reset_current_rack: bool = False):
        if reset_current_rack:
            self.rack_index = 0
        self.load_rack()

    def shuffle_rack(self):
        """Shuffle unused tiles while preserving currently staged board tiles."""
        if not self.tiles:
            return
        staged_tokens = [self.tiles[idx] for idx in self.active_rack_indices]
        remaining_tokens = [
            tok for idx, tok in enumerate(self.tiles) if idx not in self.active_rack_indices
        ]
        random.shuffle(remaining_tokens)

        new_tiles = staged_tokens + remaining_tokens
        self.tiles = new_tiles
        self.active_rack_indices = list(range(len(staged_tokens)))
        self.rack_used = [i < len(staged_tokens) for i in range(len(self.tiles))]
        self._rebuild_widgets()

    def clear_board_tiles(self):
        self.active_rack_indices = []
        self.rack_used = [False] * len(self.tiles)
        self._refresh_visuals()
        self.feedback_lbl.setText("Board cleared! Tap rack tiles to form a word.")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )

    def _rebuild_widgets(self):
        self._clear_layout(self.board_layout)
        self._clear_layout(self.rack_layout)
        self.board_buttons = []
        self.rack_buttons = []

        ml_font = self.window.ml_font_family

        for pos, r_idx in enumerate(self.active_rack_indices):
            b_btn = QPushButton(self.tiles[r_idx])
            b_btn.setObjectName("BoardTile")
            b_btn.setFont(QFont(ml_font, 26, QFont.Bold))
            b_btn.setStyleSheet(self.BOARD_TILE_STYLE)
            b_btn.clicked.connect(lambda checked=False, p=pos: self._on_board_tile_clicked(p))
            self.board_layout.addWidget(b_btn)
            self.board_buttons.append(b_btn)

        if not self.board_buttons:
            placeholder = QLabel("Tap tiles below to place them here")
            placeholder.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #2D6A4F; "
                "background: rgba(255, 255, 255, 130); padding: 14px 22px; "
                "border: 2px dashed rgba(64, 145, 108, 175); border-radius: 14px;"
            )
            self.board_layout.addWidget(placeholder)

        for r_idx, tok in enumerate(self.tiles):
            t_btn = QPushButton(tok)
            t_btn.setObjectName("RackTile")
            t_btn.setFont(QFont(ml_font, 26, QFont.Bold))
            t_btn.setEnabled(not self.rack_used[r_idx])
            t_btn.setStyleSheet(self.RACK_TILE_STYLE)
            t_btn.clicked.connect(lambda checked=False, i=r_idx: self._on_rack_tile_clicked(i))
            self.rack_layout.addWidget(t_btn)
            self.rack_buttons.append(t_btn)

        self._refresh_words_label()

    def _on_rack_tile_clicked(self, rack_idx: int):
        if rack_idx < 0 or rack_idx >= len(self.tiles) or self.rack_used[rack_idx]:
            return
        self.rack_used[rack_idx] = True
        self.active_rack_indices.append(rack_idx)
        self._rebuild_widgets()

    def _on_board_tile_clicked(self, board_pos: int):
        if board_pos < 0 or board_pos >= len(self.active_rack_indices):
            return
        rack_idx = self.active_rack_indices.pop(board_pos)
        self.rack_used[rack_idx] = False
        self._rebuild_widgets()

    def _refresh_visuals(self):
        for r_idx, btn in enumerate(self.rack_buttons):
            if r_idx < len(self.rack_used):
                btn.setEnabled(not self.rack_used[r_idx])
                btn.setStyleSheet(self.RACK_TILE_STYLE)

    def _refresh_words_label(self):
        if not self.scored_words:
            self.words_lbl.setText(f"Words Made: —   |   Scrabble Score: {self.scrabble_points}")
        else:
            joined = "   •   ".join(self.scored_words)
            self.words_lbl.setText(
                f"Words Made ({len(self.scored_words)}): {joined}   |   Score: {self.scrabble_points}"
            )

    def submit_word(self):
        formed = "".join(self.tiles[i] for i in self.active_rack_indices).strip()
        if not formed:
            self.feedback_lbl.setText("Tap at least one tile first!")
            self.feedback_lbl.setStyleSheet(
                "font-size: 17px; font-weight: bold; color: #D9534F; background: transparent;"
            )
            return

        lookup = self._word_lookup()
        matched = lookup.get(formed)
        if matched:
            pts = max(1, len(self.active_rack_indices))
            self.scrabble_points += pts
            self.window.add_stars(1)

            en = matched.get("en") or matched.get("meaning") or ""
            label = f"{formed} ({en})" if en else formed
            if label not in self.scored_words:
                self.scored_words.append(label)

            self.feedback_lbl.setText(f"🎉 Great word! +{pts} pts:  {label}")
            self.feedback_lbl.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #1B7A43; background: transparent;"
            )
            if matched.get("id"):
                self.window.play_audio(matched["id"])

            self.active_rack_indices = []
            self.rack_used = [False] * len(self.tiles)
            self._rebuild_widgets()
        else:
            self.feedback_lbl.setText(
                f"'{formed}' isn't in the word list yet—tap a staged tile to remove it or press Clear."
            )
            self.feedback_lbl.setStyleSheet(
                "font-size: 17px; font-weight: bold; color: #D9534F; background: transparent;"
            )

    def show_reloaded_feedback(self):
        self.feedback_lbl.setText("🔄 Reloaded CSV data.")
        self.feedback_lbl.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #1B4332; background: transparent;"
        )