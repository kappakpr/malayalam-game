# Malayalam Games — Interactive Malayalam learning games (Modular Entry Point)
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import math
import os
from pathlib import Path
import sys
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from audio_manager import AudioManager
from csv_vocab import (
    CSV_DIR,
    ensure_game_csvs,
    load_letter_tracing_csv,
    load_scrabble_racks_csv,
    load_word_builder_csv,
    load_word_match_csv,
)
from custom_vocab import load_custom_vocab
from pages.add_word_page import AddWordPage
from pages.builder_page import WordBuilderPage
from pages.match_page import MatchPage
from pages.scrabble_page import ScrabblePage
from pages.tracing_page import TracingPage
from ui_styles import (
    create_twinkling_stars,
    draw_four_point_star,
    make_action_button,
    make_kid_pattern_tile,
)


def resource_path(relative_path: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_dir / relative_path


class ModeTabButton(QPushButton):
    """Mode tab button that reliably renders dark green with white text when checked."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("ModeTab")
        self.setCheckable(True)
        self.setFocusPolicy(Qt.NoFocus)

    def paintEvent(self, event):
        if not self.isChecked():
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor("#1B4332"), 2))
        painter.setBrush(QColor("#1B4332"))
        painter.drawRoundedRect(rect, 10, 10)

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())


class MalayalamGamesWindow(QMainWindow):
    """Top-level window coordinating game modes, shared CSV pools, stars, and audio."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("മലയാളം പഠിക്കാം — Learn Malayalam")
        self.setFixedSize(980, 620)
        self._bg_tile = make_kid_pattern_tile(128)

        self.ml_font_family = self._load_malayalam_font()
        self.score = 0

        self.vocab_items: list[dict] = []
        self.trace_letters: list[dict] = []
        self.word_puzzles: list[dict] = []
        self.scrabble_racks: list[dict] = []

        self.audio = AudioManager(self, parent=self)
        self.audio.say_phrase("Try again", voice="en-US-AriaNeural", play_immediately=False)

        self._setup_ui()
        self.refresh_vocab_pool(reset_round=True)

        self._stars = create_twinkling_stars(1040, 620, count=22)
        self._start_time = time.monotonic()

        self._twinkle_timer = QTimer(self)
        self._twinkle_timer.setInterval(90)
        self._twinkle_timer.timeout.connect(self._on_twinkle_tick)
        self._twinkle_timer.start()

    def _on_twinkle_tick(self):
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#E8F6FF"))   # clearer morning sky
        grad.setColorAt(0.55, QColor("#FFF9E6"))  # warm cream
        grad.setColorAt(1.0, QColor("#E3F5EA"))   # gentle meadow tint
        painter.fillRect(self.rect(), grad)

        if not self._bg_tile.isNull():
            painter.drawTiledPixmap(self.rect(), self._bg_tile)

        elapsed = time.monotonic() - self._start_time
        w = float(self.width())
        h = float(self.height())

        for star in self._stars:
            wave = 0.5 + 0.5 * math.sin(elapsed * star["speed"] + star["phase"])
            shine = wave ** 1.8
            alpha = int(
                star["min_alpha"] + shine * (star["max_alpha"] - star["min_alpha"])
            )
            scale = 0.78 + 0.35 * shine
            r, g, b = star["rgb"]
            color = QColor(r, g, b, alpha)
            draw_four_point_star(
                painter,
                cx=star["x_ratio"] * w,
                cy=star["y_ratio"] * h,
                outer_r=star["outer_r"] * scale,
                inner_r=star["inner_r"] * scale,
                color=color,
                glow_strength=shine,
            )

        super().paintEvent(event)

    def add_stars(self, points: int):
        self.score += points
        self.score_lbl.setText(f"⭐ Stars: {self.score}")

    def play_audio(self, file_id: str, followup_phrase: tuple[str, str] | None = None):
        self.audio.play_audio(file_id, followup_phrase=followup_phrase)

    def say_phrase(self, text: str, voice: str = "en-US-AriaNeural", play_immediately: bool = True):
        self.audio.say_phrase(text, voice=voice, play_immediately=play_immediately)

    def closeEvent(self, event):
        self.audio.shutdown()
        super().closeEvent(event)

    def _load_malayalam_font(self) -> str:
        font_path = resource_path("assets/fonts/NotoSansMalayalam-Bold.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        for candidate in ("Kohinoor Malayalam", "Malayalam Sangam MN", "Arial Unicode MS"):
            if candidate in QFontDatabase.families():
                return candidate
        return QApplication.font().family()

    def _on_reload_csv_clicked(self):
        ensure_game_csvs(force_reset=False)
        self.refresh_vocab_pool(reset_round=False)
        if hasattr(self, "add_word_page"):
            self.add_word_page.load_csv_into_editor()
            if hasattr(self.add_word_page, "show_reloaded_feedback"):
                self.add_word_page.show_reloaded_feedback()

    def _on_reset_csv_clicked(self):
        ensure_game_csvs(force_reset=True)
        self.refresh_vocab_pool(reset_round=True)
        if hasattr(self, "add_word_page"):
            self.add_word_page.load_csv_into_editor()
            if hasattr(self.add_word_page, "_set_status"):
                self.add_word_page._set_status("♻️ Reset CSV files to bundled defaults.", color="#2D6A4F")

    def _setup_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F7F4;
            }
            QPushButton#ModeTab {
                background-color: rgba(224, 236, 231, 225);
                color: #1B4332;
                border-style: solid;
                border-width: 2px;
                border-color: #95D5B2;
                border-radius: 10px;
                padding: 5px 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#ModeTab:hover {
                background-color: #CCE3DA;
                color: #1B4332;
                border-color: #40916C;
            }
            QPushButton#WordCard {
                background-color: #FFFFFF;
                color: #1B4332;
                border-style: solid;
                border-width: 3px;
                border-color: #B7E4C7;
                border-radius: 20px;
                padding: 6px;
            }
            QPushButton#WordCard:hover {
                background-color: #E8F8F0;
                color: #1B4332;
                border-style: solid;
                border-width: 3px;
                border-color: #40916C;
            }
            QPushButton#ActionBtn {
                background-color: #FF8C42;
                color: #FFFFFF;
                border-style: solid;
                border-width: 0px;
                border-radius: 14px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#ActionBtn:hover {
                background-color: #F27424;
                color: #FFFFFF;
            }
        """)

        central = QWidget()
        central.setAttribute(Qt.WA_TranslucentBackground, True)
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(6)

        self.title_lbl = QLabel("മലയാളം പഠിക്കാം")
        self.title_lbl.setFont(QFont(self.ml_font_family, 15, QFont.Bold))
        self.title_lbl.setStyleSheet("color: #1B4332; background: transparent;")
        self.title_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.tab_match = ModeTabButton("🎯 Match")
        self.tab_match.setChecked(True)

        self.tab_trace = ModeTabButton("✍️ Tracing")
        self.tab_words = ModeTabButton("🧩 Builder")
        self.tab_scrabble = ModeTabButton("🎲 Scrabble")
        self.tab_add = ModeTabButton("➕ Add Word")

        self.reload_csv_btn = make_action_button(
            "🔄 Reload CSV",
            self._on_reload_csv_clicked,
            variant="orange",
            min_height=32,
        )
        self.reset_csv_btn = make_action_button(
            "♻️ Reset CSV",
            self._on_reset_csv_clicked,
            variant="green",
            min_height=32,
        )

        for tab in (
            self.tab_match,
            self.tab_trace,
            self.tab_words,
            self.tab_scrabble,
            self.tab_add,
            self.reload_csv_btn,
            self.reset_csv_btn,
        ):
            tab.setMinimumHeight(32)
            tab.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.tab_match.clicked.connect(lambda: self.switch_mode(0))
        self.tab_trace.clicked.connect(lambda: self.switch_mode(1))
        self.tab_words.clicked.connect(lambda: self.switch_mode(2))
        self.tab_scrabble.clicked.connect(lambda: self.switch_mode(3))
        self.tab_add.clicked.connect(lambda: self.switch_mode(4))

        self.score_lbl = QLabel("⭐ Stars: 0")
        self.score_lbl.setMinimumHeight(36)
        self.score_lbl.setStyleSheet(
            "background: #FFE66D; color: #5C4700; padding: 7px 13px; "
            "border-radius: 12px; font-size: 14px; font-weight: bold;"
        )

        header.addWidget(self.title_lbl)
        header.addSpacing(6)
        header.addWidget(self.tab_match)
        header.addWidget(self.tab_trace)
        header.addWidget(self.tab_words)
        header.addWidget(self.tab_scrabble)
        header.addWidget(self.tab_add)
        header.addStretch()
        header.addWidget(self.reload_csv_btn)
        header.addWidget(self.reset_csv_btn)
        header.addWidget(self.score_lbl)
        root.addLayout(header)

        self.match_page = MatchPage(self)
        self.tracing_page = TracingPage(self)
        self.builder_page = WordBuilderPage(self)
        self.scrabble_page = ScrabblePage(self)
        self.add_word_page = AddWordPage(self)

        self.stack = QStackedWidget()
        self.stack.setAttribute(Qt.WA_TranslucentBackground, True)
        self.stack.setStyleSheet("background: transparent;")
        self.stack.addWidget(self.match_page)
        self.stack.addWidget(self.tracing_page)
        self.stack.addWidget(self.builder_page)
        self.stack.addWidget(self.scrabble_page)
        self.stack.addWidget(self.add_word_page)
        root.addWidget(self.stack)

        footer = QHBoxLayout()
        footer.addStretch()
        credit_lbl = QLabel('Game Concept by "Kududu & Kukudu"')
        credit_lbl.setAttribute(Qt.WA_TranslucentBackground, True)
        credit_lbl.setStyleSheet(
            "color: #40916C; font-size: 12px; font-style: italic; "
            "font-weight: bold; background: transparent;"
        )
        footer.addWidget(credit_lbl)
        footer.addStretch()
        root.addLayout(footer)

    def switch_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        tabs = (
            self.tab_match,
            self.tab_trace,
            self.tab_words,
            self.tab_scrabble,
            self.tab_add,
        )
        for i, tab in enumerate(tabs):
            tab.setChecked(i == index)
            tab.update()

        if index == 1 and hasattr(self.tracing_page, "load_letter"):
            self.tracing_page.load_letter()
        elif index == 2 and hasattr(self.builder_page, "load_puzzle"):
            self.builder_page.load_puzzle()
        elif index == 3 and hasattr(self.scrabble_page, "tiles"):
            if not self.scrabble_page.tiles:
                self.scrabble_page.load_rack()
            elif hasattr(self.scrabble_page, "refresh_ui"):
                self.scrabble_page.refresh_ui()
        elif index == 4 and hasattr(self.add_word_page, "sync_categories"):
            self.add_word_page.sync_categories()

    def refresh_vocab_pool(self, reset_round: bool = False):
        self.vocab_items = load_word_match_csv() + load_custom_vocab()
        self.trace_letters = load_letter_tracing_csv()
        self.word_puzzles = load_word_builder_csv()
        self.scrabble_racks = load_scrabble_racks_csv()
        self.match_page.rebuild_categories()
        if hasattr(self.add_word_page, "sync_categories"):
            self.add_word_page.sync_categories()
        if reset_round:
            self.match_page.next_round()

    def _refresh_all_pages_state(self, reset_match_round: bool = False):
        self.refresh_vocab_pool(reset_round=reset_match_round)
        if hasattr(self.tracing_page, "letter_index"):
            self.tracing_page.letter_index = 0
        if hasattr(self.tracing_page, "on_letters_reloaded"):
            self.tracing_page.on_letters_reloaded()
        if hasattr(self.builder_page, "puzzle_index"):
            self.builder_page.puzzle_index = 0
        if hasattr(self.builder_page, "on_puzzles_reloaded"):
            self.builder_page.on_puzzles_reloaded()
        if hasattr(self.scrabble_page, "rack_index"):
            self.scrabble_page.rack_index = 0
        if hasattr(self.scrabble_page, "on_racks_reloaded"):
            self.scrabble_page.on_racks_reloaded(reset_current_rack=True)
        if hasattr(self.add_word_page, "load_csv_into_editor"):
            self.add_word_page.load_csv_into_editor()

    def _reload_all_csvs(self):
        self.refresh_vocab_pool(reset_round=False)
        if hasattr(self.tracing_page, "on_letters_reloaded"):
            self.tracing_page.on_letters_reloaded()
        if hasattr(self.builder_page, "on_puzzles_reloaded"):
            self.builder_page.on_puzzles_reloaded()
        if hasattr(self.scrabble_page, "on_racks_reloaded"):
            self.scrabble_page.on_racks_reloaded(reset_current_rack=True)

        current_widget = self.stack.currentWidget()
        if current_widget is self.match_page:
            self.match_page.show_reloaded_feedback()
        elif current_widget is self.add_word_page and hasattr(self.add_word_page, "show_reloaded_feedback"):
            self.add_word_page.show_reloaded_feedback()

        word_count = (
            len(self.scrabble_page._word_lookup())
            if hasattr(self.scrabble_page, "_word_lookup")
            else 0
        )
        print(
            f"[CSV] Reloaded: match={len(self.vocab_items)}, "
            f"trace={len(self.trace_letters)}, puzzles={len(self.word_puzzles)}, "
            f"racks={len(self.scrabble_racks)}, words={word_count}"
        )

    def _reset_bundled_csvs(self):
        reply = QMessageBox.question(
            self,
            "Reset Bundled CSVs",
            f"Overwrite all CSV files in:\n{CSV_DIR}\n\n"
            "with the bundled starter CSVs from assets/csv?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        ensure_game_csvs(force_reset=True)
        self._refresh_all_pages_state(reset_match_round=True)

        current_widget = self.stack.currentWidget()
        msg = "♻️ Reset all CSV files from bundled templates."
        if current_widget is self.match_page:
            self.match_page.feedback_lbl.setText(msg)
            self.match_page.feedback_lbl.setStyleSheet(
                "font-size: 17px; font-weight: bold; color: #2D6A4F; background: transparent;"
            )
        elif current_widget is self.tracing_page and hasattr(self.tracing_page, "load_letter"):
            self.tracing_page.load_letter()
        elif current_widget is self.builder_page and hasattr(self.builder_page, "feedback_lbl"):
            self.builder_page.feedback_lbl.setText(msg)
            self.builder_page.feedback_lbl.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #2D6A4F; background: transparent;"
            )
        elif current_widget is self.scrabble_page and hasattr(self.scrabble_page, "feedback_lbl"):
            self.scrabble_page.feedback_lbl.setText(msg)
            self.scrabble_page.feedback_lbl.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #2D6A4F; background: transparent;"
            )
        elif current_widget is self.add_word_page and hasattr(self.add_word_page, "status_lbl"):
            self.add_word_page.status_lbl.setText(msg)
            self.add_word_page.status_lbl.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #1B7A43; border: none;"
            )


def main():
    app = QApplication(sys.argv)
    window = MalayalamGamesWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()