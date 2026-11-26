# Malayalam Games — Inline CSV Vocabulary Editor Page
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import csv
import io
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from audio_manager import AudioGenWorker
from csv_vocab import CSV_HEADERS, WORD_MATCH_CSV, ensure_game_csvs
from custom_vocab import slugify_id


class AddWordPage(QWidget):
    """Direct CSV editor page for bulk-editing word_match.csv."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self._audio_queue: list[tuple[str, str]] = []
        self._audio_total = 0
        self._audio_saved = 0
        self._audio_failed = 0
        self._build_ui()
        self.load_csv_into_editor()

    def _build_ui(self):
        ml_font = self.window.ml_font_family
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        card = QFrame()
        card.setStyleSheet(
            "background: #FFFFFF; border-radius: 18px; border: 2px solid #D8F3DC;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(10)

        header_row = QHBoxLayout()
        heading = QLabel("Edit Vocabulary CSV (word_match.csv)")
        heading.setStyleSheet("font-size: 19px; font-weight: bold; color: #1B4332; border: none;")

        self.path_lbl = QLabel(str(WORD_MATCH_CSV))
        self.path_lbl.setStyleSheet("font-size: 12px; color: #52796F; border: none;")
        self.path_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        header_row.addWidget(heading)
        header_row.addStretch()
        header_row.addWidget(self.path_lbl)
        card_layout.addLayout(header_row)

        help_lbl = QLabel(
            "Columns: id,ml,en,emoji,cat  —  type or paste multiple rows directly, then click Save CSV."
        )
        help_lbl.setStyleSheet("font-size: 13px; color: #2D6A4F; border: none;")
        card_layout.addWidget(help_lbl)

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont(ml_font, 15))
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.editor.setStyleSheet(
            "QPlainTextEdit {"
            "  background-color: #FAFDFB;"
            "  color: #1B4332;"
            "  border: 2px solid #B7E4C7;"
            "  border-radius: 12px;"
            "  padding: 10px;"
            "}"
        )
        card_layout.addWidget(self.editor, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        revert_btn = QPushButton("↩ Revert from File")
        revert_btn.setObjectName("ActionBtn")
        revert_btn.clicked.connect(self.load_csv_into_editor)

        external_btn = QPushButton("📝 Open in External Editor")
        external_btn.setObjectName("ActionBtn")
        external_btn.clicked.connect(self._open_in_external_editor)

        audio_btn = QPushButton("🔊 Generate Missing Audio")
        audio_btn.setObjectName("ActionBtn")
        audio_btn.clicked.connect(self._generate_missing_audio)

        save_btn = QPushButton("💾 Save CSV")
        save_btn.setObjectName("ActionBtn")
        save_btn.setStyleSheet(
            "background-color: #2D6A4F; color: #FFFFFF; border-radius: 14px; "
            "padding: 10px 20px; font-size: 14px; font-weight: bold;"
        )
        save_btn.clicked.connect(self._save_csv)

        btn_row.addWidget(revert_btn)
        btn_row.addWidget(external_btn)
        btn_row.addStretch()
        btn_row.addWidget(audio_btn)
        btn_row.addWidget(save_btn)
        card_layout.addLayout(btn_row)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D6A4F; border: none;")
        card_layout.addWidget(self.status_lbl)

        layout.addWidget(card)

    def _open_in_external_editor(self):
        ensure_game_csvs()
        resolved_path = WORD_MATCH_CSV.resolve()
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(resolved_path)))
        if opened:
            self.status_lbl.setText(f"Opened {resolved_path} in external editor. Click Revert after saving.")
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1B7A43; border: none;")
        else:
            self.status_lbl.setText(f"Could not launch an external editor for {resolved_path}.")
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #D9534F; border: none;")

    def sync_categories(self):
        """Hook kept for compatibility with MalayalamGameWindow."""
        self.path_lbl.setText(str(WORD_MATCH_CSV))

    def load_csv_into_editor(self):
        ensure_game_csvs()
        self.path_lbl.setText(str(WORD_MATCH_CSV))
        if WORD_MATCH_CSV.exists():
            text = WORD_MATCH_CSV.read_text(encoding="utf-8-sig")
        else:
            text = ",".join(CSV_HEADERS["word_match.csv"]) + "\n"
        self.editor.setPlainText(text)
        self.status_lbl.setText("Loaded word_match.csv")
        self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D6A4F; border: none;")

    def show_reloaded_feedback(self):
        self.load_csv_into_editor()
        self.status_lbl.setText("🔄 Reloaded word_match.csv")
        self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D6A4F; border: none;")

    def _validate_rows(self, raw_text: str) -> tuple[int, list[str]]:
        valid_count = 0
        issues: list[str] = []
        reader = csv.DictReader(io.StringIO(raw_text))
        if not reader.fieldnames or not {"ml", "en"}.issubset({c.strip() for c in reader.fieldnames if c}):
            issues.append("Header must include at least 'ml' and 'en' columns.")
            return 0, issues

        for line_no, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue
            ml = (row.get("ml") or "").strip()
            en = (row.get("en") or "").strip()
            if not ml or not en:
                issues.append(f"Row {line_no}: missing 'ml' or 'en'.")
            else:
                valid_count += 1
        return valid_count, issues

    def _save_csv(self):
        ensure_game_csvs()
        raw_text = self.editor.toPlainText()
        valid_count, issues = self._validate_rows(raw_text)

        if issues and valid_count == 0:
            self.status_lbl.setText(" / ".join(issues))
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #D9534F; border: none;")
            return

        WORD_MATCH_CSV.write_text(raw_text, encoding="utf-8-sig")
        self.window.refresh_vocab_pool(reset_round=False)

        if issues:
            self.status_lbl.setText(
                f"Saved {valid_count} valid row(s), with note: {' / '.join(issues)}"
            )
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #D9534F; border: none;")
        else:
            self.status_lbl.setText(f"💾 Saved word_match.csv ({valid_count} word(s) active in Match & Scrabble).")
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1B7A43; border: none;")

    def _collect_missing_audio_rows(self) -> list[tuple[str, str]]:
        from audio_manager import AUDIO_DIR
        from custom_vocab import CUSTOM_AUDIO_DIR

        missing: list[tuple[str, str]] = []
        seen_ids: set[str] = set()
        reader = csv.DictReader(io.StringIO(self.editor.toPlainText()))
        for row in reader:
            ml = (row.get("ml") or "").strip()
            en = (row.get("en") or "").strip()
            if not ml or not en:
                continue
            item_id = (row.get("id") or "").strip() or slugify_id(en or ml)
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            exists = any(
                p.exists() and p.stat().st_size > 0
                for p in (CUSTOM_AUDIO_DIR / f"{item_id}.mp3", Path(AUDIO_DIR) / f"{item_id}.mp3")
            )
            if not exists:
                missing.append((item_id, ml))
        return missing

    def _generate_missing_audio(self):
        if self._audio_queue:
            self.status_lbl.setText("Audio batch generation is already running...")
            return

        self._save_csv()
        missing = self._collect_missing_audio_rows()
        if not missing:
            self.status_lbl.setText("All vocabulary rows already have MP3 audio files.")
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1B7A43; border: none;")
            return

        self._audio_queue = list(missing)
        self._audio_total = len(missing)
        self._audio_saved = 0
        self._audio_failed = 0
        self._run_next_audio_job()

    def _run_next_audio_job(self):
        if not self._audio_queue:
            self.status_lbl.setText(
                f"Audio finished: {self._audio_saved} generated, {self._audio_failed} failed (of {self._audio_total})."
            )
            color = "#1B7A43" if self._audio_failed == 0 else "#D9534F"
            self.status_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color}; border: none;")
            return

        item_id, ml_text = self._audio_queue.pop(0)
        done_so_far = self._audio_total - len(self._audio_queue)
        self.status_lbl.setText(f"Generating audio ({done_so_far}/{self._audio_total}): {item_id}...")
        self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D6A4F; border: none;")

        worker = AudioGenWorker(item_id, ml_text, parent=self)
        worker.finished_with_status.connect(self._on_batch_audio_done)
        self.window.audio.register_worker(worker)

    def _on_batch_audio_done(self, ok: bool, _msg: str):
        if ok:
            self._audio_saved += 1
        else:
            self._audio_failed += 1
        self._run_next_audio_job()