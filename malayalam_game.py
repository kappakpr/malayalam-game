from pathlib import Path
import sys
import os
import asyncio
import os
from pathlib import Path
import random
import sys

import edge_tts
from PySide6.QtCore import Qt, QUrl, QPoint, QRect, QThread, Signal, QEvent, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QPainter, QPen, QColor, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QStackedWidget,
    QFrame,
    QScrollArea,
)

from vocab_data import VOCAB_ITEMS, TRACE_LETTERS
from custom_vocab import (
    CUSTOM_AUDIO_DIR,
    USER_DATA_DIR,
    load_custom_vocab,
    save_custom_vocab,
    slugify_id,
)


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def resource_path(relative_path: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_dir / relative_path

AUDIO_DIR = resource_path(os.path.join("assets", "audio"))
CACHE_AUDIO_DIR = USER_DATA_DIR / "cache"


class PhraseSpeakWorker(QThread):
    ready_to_play = Signal(str)

    def __init__(self, text: str, voice: str = "en-US-AriaNeural", parent=None):
        super().__init__(parent)
        self.text = text
        self.voice = voice

    def run(self):
        try:
            CACHE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            safe_name = slugify_id(f"{self.voice}_{self.text}")
            out_path = CACHE_AUDIO_DIR / f"{safe_name}.mp3"

            async def _gen():
                comm = edge_tts.Communicate(self.text, self.voice)
                await comm.save(str(out_path))

            asyncio.run(_gen())
            if out_path.exists() and out_path.stat().st_size > 0:
                self.ready_to_play.emit(str(out_path.resolve()))
        except Exception as exc:
            print(f"[Phrase TTS Error] {exc}")


class AudioGenWorker(QThread):
    finished_with_status = Signal(bool, str)

    def __init__(self, file_id: str, ml_text: str, parent=None):
        super().__init__(parent)
        self.file_id = file_id
        self.ml_text = ml_text

    def run(self):
        try:
            CUSTOM_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            out_path = CUSTOM_AUDIO_DIR / f"{self.file_id}.mp3"

            async def _gen():
                comm = edge_tts.Communicate(self.ml_text, "ml-IN-SobhanaNeural", rate="-15%")
                await comm.save(str(out_path))

            asyncio.run(_gen())
            self.finished_with_status.emit(True, f"Saved word and generated {self.file_id}.mp3")
        except Exception as exc:
            self.finished_with_status.emit(False, f"Saved word (audio skipped: {exc})")


class TracingCanvas(QWidget):
    """Interactive drawing pad with a ghosted Malayalam guide character."""

    def __init__(self, ml_font_family: str, parent=None):
        super().__init__(parent)
        self.setMinimumSize(460, 340)
        self.ml_font_family = ml_font_family
        self.guide_char = "അ"
        self.pen_color = QColor("#E65100")
        self.pen_width = 18
        self.last_point = QPoint()
        self.drawing = False
        self.canvas_pixmap = QPixmap(640, 380)
        self.canvas_pixmap.fill(Qt.transparent)

    def set_character(self, char: str):
        self.guide_char = char
        self.clear_drawing()

    def set_pen_color(self, hex_color: str):
        self.pen_color = QColor(hex_color)

    def clear_drawing(self):
        self.canvas_pixmap.fill(Qt.transparent)
        self.update()

    def resizeEvent(self, event):
        if event.size().width() > 0 and event.size().height() > 0:
            new_pix = QPixmap(event.size())
            new_pix.fill(Qt.transparent)
            painter = QPainter(new_pix)
            painter.drawPixmap(0, 0, self.canvas_pixmap)
            painter.end()
            self.canvas_pixmap = new_pix
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = event.position().toPoint()
            self.drawing = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            current = event.position().toPoint()
            painter = QPainter(self.canvas_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, current)
            painter.end()
            self.last_point = current
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(6, 6, -6, -6)
        painter.setBrush(QColor("#FFFDF7"))
        painter.setPen(QPen(QColor("#FFB74D"), 3, Qt.DashLine))
        painter.drawRoundedRect(rect, 20, 20)

        mid_y = self.height() // 2 + 55
        painter.setPen(QPen(QColor("#E0E0E0"), 2, Qt.DotLine))
        painter.drawLine(40, mid_y, self.width() - 40, mid_y)

        guide_font = QFont(self.ml_font_family, 165, QFont.Bold)
        painter.setFont(guide_font)
        painter.setPen(QColor("#DCE6F2"))
        painter.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignCenter, self.guide_char)

        painter.drawPixmap(0, 0, self.canvas_pixmap)
        painter.end()


class MalayalamGameWindow(QMainWindow):
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
            background-color: #FFFFFF;
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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("മലയാളം പഠിക്കാം — Learn Malayalam")
        self.setFixedSize(980, 680)

        self.ml_font_family = self._load_malayalam_font()
        self.score = 0
        self.current_target = None
        self.current_choices = []
        self.selected_category = "All"
        self.trace_index = 0
        self.vocab_items = list(VOCAB_ITEMS) + load_custom_vocab()
        self._audio_worker = None
        self._phrase_worker = None
        self._pending_followup_phrase = None
        self._followup_triggered = False
        self._prompt_hovered = False

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.9)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self._on_audio_error)
        self.player.positionChanged.connect(self._on_audio_position_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

        self.say_phrase("Try again", voice="en-US-AriaNeural", play_immediately=False)

        self._setup_ui()
        self._refresh_vocab_pool(reset_round=True)

    def _on_audio_error(self, error, error_string: str):
        print(f"[Audio Error] {error}: {error_string}")

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

    def _load_malayalam_font(self) -> str:
        font_path = resource_path(os.path.join("assets", "fonts", "NotoSansMalayalam-Bold.ttf"))
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
        for candidate in ("Kohinoor Malayalam", "Malayalam Sangam MN", "Arial Unicode MS"):
            if candidate in QFontDatabase.families():
                return candidate
        return QApplication.font().family()

    def play_audio(self, file_id: str, followup_phrase: tuple[str, str] | None = None):
        self._pending_followup_phrase = followup_phrase
        self._followup_triggered = False
        candidates = [
            CUSTOM_AUDIO_DIR / f"{file_id}.mp3",
            Path(AUDIO_DIR) / f"{file_id}.mp3",
        ]
        mp3_path = next(
            (str(p.resolve()) for p in candidates if p.exists() and p.stat().st_size > 0),
            None,
        )
        print(f"[Audio] id={file_id!r} path={mp3_path!r} found={bool(mp3_path)}")
        if not mp3_path:
            if self._pending_followup_phrase:
                phrase, voice = self._pending_followup_phrase
                self._pending_followup_phrase = None
                self.say_phrase(phrase, voice=voice)
            return

        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(mp3_path))
        self.player.play()

    def _setup_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F7F4;
            }
            QPushButton#ModeTab {
                background-color: #E0ECE7;
                color: #1B4332;
                border-style: solid;
                border-width: 0px;
                border-radius: 14px;
                padding: 10px 18px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#ModeTab:hover {
                background-color: #CCE3DA;
                color: #1B4332;
            }
            QPushButton#ModeTab:checked {
                background-color: #2D6A4F;
                color: #FFFFFF;
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
                padding: 10px 20px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#ActionBtn:hover {
                background-color: #F27424;
                color: #FFFFFF;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_lbl = QLabel("🌴 മലയാളം പഠിക്കാം")
        title_lbl.setFont(QFont(self.ml_font_family, 22, QFont.Bold))
        title_lbl.setStyleSheet("color: #1B4332;")

        self.tab_match = QPushButton("🎯 Word Match")
        self.tab_match.setObjectName("ModeTab")
        self.tab_match.setCheckable(True)
        self.tab_match.setChecked(True)

        self.tab_trace = QPushButton("✍️ Letter Tracing")
        self.tab_trace.setObjectName("ModeTab")
        self.tab_trace.setCheckable(True)

        self.tab_add = QPushButton("➕ Add Word")
        self.tab_add.setObjectName("ModeTab")
        self.tab_add.setCheckable(True)

        self.tab_match.clicked.connect(lambda: self.switch_mode(0))
        self.tab_trace.clicked.connect(lambda: self.switch_mode(1))
        self.tab_add.clicked.connect(lambda: self.switch_mode(2))

        self.score_lbl = QLabel("⭐ Stars: 0")
        self.score_lbl.setStyleSheet(
            "background: #FFE66D; color: #5C4700; padding: 8px 16px; "
            "border-radius: 14px; font-size: 16px; font-weight: bold;"
        )

        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self.tab_match)
        header.addWidget(self.tab_trace)
        header.addWidget(self.tab_add)
        header.addStretch()
        header.addWidget(self.score_lbl)
        root.addLayout(header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_word_match_page())
        self.stack.addWidget(self._build_tracing_page())
        self.stack.addWidget(self._build_add_word_page())
        root.addWidget(self.stack)

    def switch_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        self.tab_match.setChecked(index == 0)
        self.tab_trace.setChecked(index == 1)
        self.tab_add.setChecked(index == 2)
        if index == 1:
            self._load_trace_letter()
        elif index == 2:
            self._sync_category_combo()

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

    def _rebuild_category_buttons(self):
        self._clear_layout(self.cat_bar)
        self.cat_buttons = {}
        categories = ["All"] + list(dict.fromkeys(item["cat"] for item in self.vocab_items))
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

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._update_cat_arrows)

    def _sync_category_combo(self):
        existing_cats = list(dict.fromkeys(item["cat"] for item in self.vocab_items))
        current_text = self.new_cat_combo.currentText()
        self.new_cat_combo.clear()
        self.new_cat_combo.addItems(existing_cats)
        if current_text:
            self.new_cat_combo.setEditText(current_text)

    def _refresh_vocab_pool(self, reset_round: bool = False):
        self.vocab_items = list(VOCAB_ITEMS) + load_custom_vocab()
        self._rebuild_category_buttons()
        self._sync_category_combo()
        if reset_round:
            self.next_word_round()

    def eventFilter(self, obj, event):
        if obj is self.prompt_lbl:
            if event.type() == QEvent.Enter:
                self._prompt_hovered = True
                self._update_prompt_display(True)
            elif event.type() == QEvent.Leave:
                self._prompt_hovered = False
                self._update_prompt_display(False)
        return super().eventFilter(obj, event)

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

    def _build_word_match_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        cat_row = QHBoxLayout()
        cat_row.setSpacing(6)

        arrow_style = """
            QPushButton#CatArrow {
                background-color: #FFFFFF;
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
                background-color: #EAF2EE;
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
        self.cat_scroll.setStyleSheet("background: transparent;")

        self.cat_container = QWidget()
        self.cat_container.setStyleSheet("background: transparent;")
        self.cat_bar = QHBoxLayout(self.cat_container)
        self.cat_bar.setContentsMargins(0, 2, 0, 2)
        self.cat_bar.setSpacing(8)

        self.cat_buttons = {}
        self._rebuild_category_buttons()
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
        banner.setStyleSheet("background: #FFFFFF; border-radius: 18px; border: 2px solid #D8F3DC;")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(20, 14, 20, 14)

        self.prompt_lbl = QLabel("Find: ...")
        self.prompt_lbl.setFont(QFont(self.ml_font_family, 24, QFont.Bold))
        self.prompt_lbl.setStyleSheet("color: #1B4332;")
        self.prompt_lbl.setAttribute(Qt.WA_Hover, True)
        self.prompt_lbl.installEventFilter(self)

        hear_btn = QPushButton("🔊 Hear Word")
        hear_btn.setObjectName("ActionBtn")
        hear_btn.setMinimumSize(170, 46)
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
            lambda: self.play_audio(self.current_target["id"]) if self.current_target else None
        )

        banner_layout.addWidget(self.prompt_lbl)
        banner_layout.addStretch()
        banner_layout.addWidget(hear_btn)
        layout.addWidget(banner)

        grid_wrapper = QHBoxLayout()
        grid_wrapper.addStretch(1)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)
        self.card_buttons = []
        self.card_widgets = []

        for idx in range(4):
            btn = QPushButton()
            btn.setObjectName("WordCard")
            btn.setFixedSize(360, 165)
            btn.clicked.connect(lambda checked, i=idx: self.check_word_answer(i))

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
            ml_lbl.setFont(QFont(self.ml_font_family, 28, QFont.Bold))
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
        self.feedback_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #2D6A4F;")
        layout.addWidget(self.feedback_lbl)

        return page

    def set_category(self, category: str):
        self.selected_category = category
        for cat, btn in self.cat_buttons.items():
            self._style_cat_button(btn, cat == category)
        self.next_word_round()

    def next_word_round(self):
        pool = (
            self.vocab_items
            if self.selected_category == "All"
            else [w for w in self.vocab_items if w["cat"] == self.selected_category]
        )
        if not pool:
            return
        choices = random.sample(pool, min(4, len(pool)))
        self.current_target = random.choice(choices)
        self.current_choices = choices

        self._update_prompt_display(self._prompt_hovered)
        self.feedback_lbl.setText("Tap the matching card!")
        self.feedback_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #2D6A4F;")

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

        self.play_audio(self.current_target["id"])

    def _fire_pending_followup(self):
        if self._followup_triggered or not self._pending_followup_phrase:
            return
        self._followup_triggered = True
        phrase, voice = self._pending_followup_phrase
        self._pending_followup_phrase = None
        self.say_phrase(phrase, voice=voice)

    def _on_audio_position_changed(self, position_ms: int):
        if not self._pending_followup_phrase or self._followup_triggered:
            return
        duration_ms = self.player.duration()
        if duration_ms > 0 and position_ms >= duration_ms - 120:
            self._fire_pending_followup()

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self._fire_pending_followup()

    def say_phrase(self, text: str, voice: str = "en-US-AriaNeural", play_immediately: bool = True):
        safe_name = slugify_id(f"{voice}_{text}")
        cached_path = CACHE_AUDIO_DIR / f"{safe_name}.mp3"
        if cached_path.exists() and cached_path.stat().st_size > 0:
            if play_immediately:
                self._play_local_mp3(str(cached_path.resolve()))
            return

        self._phrase_worker = PhraseSpeakWorker(text, voice=voice, parent=self)
        if play_immediately:
            self._phrase_worker.ready_to_play.connect(self._play_local_mp3)
        self._phrase_worker.start()

    def _play_local_mp3(self, mp3_path: str):
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(mp3_path))
        self.player.play()

    def check_word_answer(self, idx: int):
        if idx >= len(self.current_choices):
            return
        chosen = self.current_choices[idx]
        if chosen["id"] == self.current_target["id"]:
            self.score += 1
            self.score_lbl.setText(f"⭐ Stars: {self.score}")
            self.feedback_lbl.setText(f"🎉 ശരിയാണ്! (Correct!)  {chosen['ml']} = {chosen['en']}")
            self.feedback_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #1B7A43;")
            self.next_word_round()
        else:
            self.feedback_lbl.setText(f"Try again! That was {chosen['ml']} ({chosen['en']}).")
            self.feedback_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #D9534F;")
            self.play_audio(
                chosen["id"],
                followup_phrase=("Try again", "en-US-AriaNeural"),
            )

    def _load_trace_letter(self):
        if not TRACE_LETTERS:
            return
        letter_item = TRACE_LETTERS[self.trace_index % len(TRACE_LETTERS)]
        self.trace_info_lbl.setText(f"Trace: {letter_item['ml']}  ({letter_item['name']})")
        self.canvas.set_character(letter_item["ml"])
        self.play_audio(letter_item["id"])

    def complete_trace_letter(self):
        self.score += 1
        self.score_lbl.setText(f"⭐ Stars: {self.score}")
        if TRACE_LETTERS:
            self.trace_index = (self.trace_index + 1) % len(TRACE_LETTERS)
        self._load_trace_letter()

    def _build_tracing_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.trace_info_lbl = QLabel("Trace: അ")
        self.trace_info_lbl.setFont(QFont(self.ml_font_family, 22, QFont.Bold))
        self.trace_info_lbl.setStyleSheet("color: #1B4332;")

        say_letter_btn = QPushButton("🔊 Hear Letter")
        say_letter_btn.setMinimumSize(130, 44)
        say_letter_btn.setObjectName("ActionBtn")
        say_letter_btn.clicked.connect(
            lambda: self.play_audio(TRACE_LETTERS[self.trace_index]["id"])
        )

        top_row.addWidget(self.trace_info_lbl)
        top_row.addStretch()
        top_row.addWidget(say_letter_btn)
        layout.addLayout(top_row)

        self.canvas = TracingCanvas(self.ml_font_family)
        layout.addWidget(self.canvas, stretch=1)

        controls = QHBoxLayout()
        for label, hex_code in [
            ("🟠 Orange", "#E65100"),
            ("🔵 Blue", "#1565C0"),
            ("🟢 Green", "#2E7D32"),
            ("🟣 Purple", "#6A1B9A"),
            ("🩷 Pink", "#FFC0CB"),
        ]:
            c_btn = QPushButton(label)
            c_btn.setStyleSheet(
                f"background: white; border: 2px solid {hex_code}; color: {hex_code}; "
                "border-radius: 12px; padding: 8px 12px; font-weight: bold;"
            )
            c_btn.clicked.connect(lambda checked, col=hex_code: self.canvas.set_pen_color(col))
            controls.addWidget(c_btn)

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
        done_btn.clicked.connect(self.complete_trace_letter)

        controls.addWidget(clear_btn)
        controls.addWidget(done_btn)
        layout.addLayout(controls)

        return page

    def _sync_suggested_id(self, text: str):
        self.new_id_input.setText(slugify_id(text))

    def _on_audio_gen_finished(self, ok: bool, status_msg: str):
        self.add_status_lbl.setText(status_msg)
        self.add_status_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {'#1B7A43' if ok else '#D9534F'}; border: none;"
        )

    def _save_custom_word(self):
        ml_text = self.new_ml_input.text().strip()
        en_text = self.new_en_input.text().strip()
        emoji_text = self.new_emoji_input.text().strip() or "🌟"
        cat_text = self.new_cat_combo.currentText().strip() or "Custom"
        item_id = self.new_id_input.text().strip() or slugify_id(en_text or ml_text)

        if not ml_text or not en_text:
            self.add_status_lbl.setText("Please enter both Malayalam and English words.")
            self.add_status_lbl.setStyleSheet(
                "font-size: 14px; font-weight: bold; color: #D9534F; border: none;"
            )
            return

        custom_list = load_custom_vocab()
        custom_list = [w for w in custom_list if w.get("id") != item_id]
        new_entry = {
            "id": item_id,
            "ml": ml_text,
            "en": en_text,
            "emoji": emoji_text,
            "cat": cat_text,
        }
        custom_list.append(new_entry)
        save_custom_vocab(custom_list)
        self._refresh_vocab_pool(reset_round=False)

        self.new_ml_input.clear()
        self.new_en_input.clear()
        self.new_emoji_input.clear()
        self.new_id_input.clear()
        self.add_status_lbl.setText(f"Saving '{en_text}' and generating Malayalam audio...")
        self.add_status_lbl.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2D6A4F; border: none;"
        )

        self._audio_worker = AudioGenWorker(item_id, ml_text, parent=self)
        self._audio_worker.finished_with_status.connect(self._on_audio_gen_finished)
        self._audio_worker.start()

    def _build_add_word_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(14)

        card = QFrame()
        card.setStyleSheet(
            "background: #FFFFFF; border-radius: 18px; border: 2px solid #D8F3DC; padding: 12px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        title = QLabel("Add Custom Malayalam Vocabulary")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1B4332; border: none;")
        card_layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        input_style = (
            "background: #F8FBF9; color: #1B4332; border: 2px solid #B7E4C7; "
            "border-radius: 10px; padding: 8px 12px; font-size: 15px;"
        )

        self.new_ml_input = QLineEdit()
        self.new_ml_input.setPlaceholderText("e.g., പുസ്തകം")
        self.new_ml_input.setFont(QFont(self.ml_font_family, 18))
        self.new_ml_input.setStyleSheet(input_style)

        self.new_en_input = QLineEdit()
        self.new_en_input.setPlaceholderText("e.g., Book")
        self.new_en_input.setStyleSheet(input_style)
        self.new_en_input.textChanged.connect(self._sync_suggested_id)

        self.new_emoji_input = QLineEdit()
        self.new_emoji_input.setPlaceholderText("e.g., 📖")
        self.new_emoji_input.setStyleSheet(input_style)

        self.new_cat_combo = QComboBox()
        self.new_cat_combo.setEditable(True)
        self.new_cat_combo.setStyleSheet(input_style)

        self.new_id_input = QLineEdit()
        self.new_id_input.setPlaceholderText("Auto-generated ID (e.g., book)")
        self.new_id_input.setStyleSheet(input_style)

        form.addRow("Malayalam:", self.new_ml_input)
        form.addRow("English:", self.new_en_input)
        form.addRow("Emoji:", self.new_emoji_input)
        form.addRow("Category:", self.new_cat_combo)
        form.addRow("Audio / ID:", self.new_id_input)
        card_layout.addLayout(form)

        save_btn = QPushButton("💾 Save Word & Generate Audio")
        save_btn.setObjectName("ActionBtn")
        save_btn.clicked.connect(self._save_custom_word)
        card_layout.addWidget(save_btn)

        self.add_status_lbl = QLabel("")
        self.add_status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D6A4F; border: none;")
        card_layout.addWidget(self.add_status_lbl)

        layout.addWidget(card)
        layout.addStretch()
        return page


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MalayalamGameWindow()
    window.show()
    sys.exit(app.exec())