# Malayalam Games — Add / Bulk Edit Vocabulary Page
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import asyncio
import csv
import io
from pathlib import Path
import re
import sys

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from csv_vocab import WORD_MATCH_CSV, ensure_game_csvs

try:
    from custom_vocab import CUSTOM_AUDIO_DIR
except ImportError:
    CUSTOM_AUDIO_DIR = Path(WORD_MATCH_CSV).resolve().parent.parent / "custom_audio"
from ui_styles import make_action_button

REQUIRED_MATCH_COLUMNS = ["id", "ml", "en", "emoji", "cat"]


class _BatchAudioWorker(QThread):
    """Generates missing Malayalam audio files in the background using edge-tts."""

    progress = Signal(str)
    finished_batch = Signal(int, int)

    def __init__(self, rows: list[dict[str, str]], audio_dir: Path, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.audio_dir = audio_dir

    @staticmethod
    def _safe_stem(row_id: str, ml_text: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", row_id.strip()).strip("_")
        if cleaned:
            return cleaned
        return f"word_{abs(hash(ml_text)) % 1_000_000}"

    async def _synthesize_all(self) -> tuple[int, int]:
        import edge_tts  # type: ignore[import-not-found]

        self.audio_dir.mkdir(parents=True, exist_ok=True)
        generated = 0
        failed = 0

        for idx, row in enumerate(self.rows, start=1):
            word_id = (row.get("id") or "").strip()
            ml_text = (row.get("ml") or "").strip()
            if not ml_text:
                continue

            stem = self._safe_stem(word_id, ml_text)
            out_path = self.audio_dir / f"{stem}.mp3"
            if out_path.exists() and out_path.stat().st_size > 0:
                continue

            self.progress.emit(f"🔊 Synthesizing {idx}/{len(self.rows)}: {ml_text}...")
            try:
                communicate = edge_tts.Communicate(ml_text, "ml-IN-SobhanaNeural")
                await communicate.save(str(out_path))
                generated += 1
            except Exception:
                failed += 1

        return generated, failed

    def run(self):
        try:
            generated, failed = asyncio.run(self._synthesize_all())
        except Exception as exc:
            self.progress.emit(f"⚠️ Audio batch error: {exc}")
            self.finished_batch.emit(0, 1)
            return
        self.finished_batch.emit(generated, failed)


class AddWordPage(QWidget):
    """Bulk CSV editor for word_match.csv with external editor and batch TTS."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.win = main_window
        self._audio_worker: _BatchAudioWorker | None = None
        self._build_ui()
        self.load_csv_into_editor()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        title = QLabel("📝 Bulk Vocabulary Editor (word_match.csv)")
        title.setFont(QFont(self.win.ml_font_family, 18, QFont.Bold))
        title.setStyleSheet("color: #1B4332;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet(
            "QFrame {"
            "  background-color: #FFFFFF;"
            "  border: 2px solid #B7E4C7;"
            "  border-radius: 16px;"
            "}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        hint = QLabel(
            "Columns: id, ml, en, emoji, cat — Edit directly below, open in an external app, "
            "generate missing audio, and save."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 13px; color: #344E41; font-weight: bold; border: none;")
        card_layout.addWidget(hint)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("id,ml,en,emoji,cat\namma,അമ്മ,Mother,👩,Family")
        editor_font = QFont(self.win.ml_font_family, 14)
        editor_font.setStyleHint(QFont.Monospace)
        self.editor.setFont(editor_font)
        self.editor.setStyleSheet(
            "QPlainTextEdit {"
            "  background-color: #F8FCFA;"
            "  color: #1B4332;"
            "  border: 2px solid #95D5B2;"
            "  border-radius: 12px;"
            "  padding: 10px;"
            "}"
        )
        card_layout.addWidget(self.editor, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        revert_btn = make_action_button(
            "↩ Revert from File",
            self.load_csv_into_editor,
            variant="orange",
        )
        external_btn = make_action_button(
            "📝 Open in External Editor",
            self._open_in_external_editor,
            variant="orange",
        )
        self.audio_btn = make_action_button(
            "🔊 Generate Missing Audio",
            self._generate_missing_audio,
            variant="orange",
        )
        save_btn = make_action_button(
            "💾 Save CSV",
            self._save_csv,
            variant="green",
        )

        btn_row.addWidget(revert_btn)
        btn_row.addWidget(external_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.audio_btn)
        btn_row.addWidget(save_btn)
        card_layout.addLayout(btn_row)

        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; border: none;")
        card_layout.addWidget(self.status_lbl)

        layout.addWidget(card, stretch=1)

    def _set_status(self, message: str, color: str = "#1B7A43"):
        self.status_lbl.setText(message)
        self.status_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {color}; border: none;"
        )

    def sync_categories(self):
        """Hook kept for mode switching and shared vocabulary pool updates."""
        if not self.editor.toPlainText().strip():
            self.load_csv_into_editor()

    def show_reloaded_feedback(self):
        self._set_status("🔄 Reloaded vocabulary CSV files from disk.", color="#2D6A4F")

    def load_csv_into_editor(self):
        ensure_game_csvs(force_reset=False)
        csv_path = Path(WORD_MATCH_CSV)
        if not csv_path.exists():
            self.editor.setPlainText(",".join(REQUIRED_MATCH_COLUMNS) + "\n")
            self._set_status("⚠️ word_match.csv not found; initialized header.", color="#C1121F")
            return

        content = csv_path.read_text(encoding="utf-8-sig")
        self.editor.setPlainText(content)
        self._set_status(f"Loaded {csv_path.name}", color="#2D6A4F")

    def _parse_and_validate_editor_csv(self) -> tuple[list[dict[str, str]], str | None]:
        raw_text = self.editor.toPlainText()
        if not raw_text.strip():
            return [], "CSV content cannot be empty."

        reader = csv.DictReader(io.StringIO(raw_text))
        if not reader.fieldnames:
            return [], "Missing CSV header row."

        normalized_headers = [h.strip() for h in reader.fieldnames if h is not None]
        missing_cols = [col for col in REQUIRED_MATCH_COLUMNS if col not in normalized_headers]
        if missing_cols:
            return [], f"Missing required columns: {', '.join(missing_cols)}"

        cleaned_rows: list[dict[str, str]] = []
        seen_ids: set[str] = set()

        for line_num, raw_row in enumerate(reader, start=2):
            row = {
                (k or "").strip(): (v or "").strip()
                for k, v in raw_row.items()
                if k is not None
            }
            if not any(row.values()):
                continue

            row_id = row.get("id", "")
            ml_val = row.get("ml", "")
            en_val = row.get("en", "")
            emoji_val = row.get("emoji", "")
            cat_val = row.get("cat", "")

            if not row_id or not ml_val or not en_val:
                return [], f"Row {line_num}: 'id', 'ml', and 'en' are required."

            if row_id in seen_ids:
                return [], f"Row {line_num}: duplicate id '{row_id}'."
            seen_ids.add(row_id)

            cleaned_rows.append(
                {
                    "id": row_id,
                    "ml": ml_val,
                    "en": en_val,
                    "emoji": emoji_val or "✨",
                    "cat": cat_val or "Custom",
                }
            )

        if not cleaned_rows:
            return [], "No valid vocabulary rows found after header."

        return cleaned_rows, None

    def _save_csv(self):
        rows, err = self._parse_and_validate_editor_csv()
        if err:
            self._set_status(f"❌ {err}", color="#C1121F")
            return

        ensure_game_csvs(force_reset=False)
        csv_path = Path(WORD_MATCH_CSV)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=REQUIRED_MATCH_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

        formatted = out.getvalue()
        csv_path.write_text(formatted, encoding="utf-8-sig")
        self.editor.setPlainText(formatted)

        if hasattr(self.win, "refresh_vocab_pool"):
            self.win.refresh_vocab_pool(reset_round=False)

        self._set_status(f"✅ Saved {len(rows)} words to {csv_path.name}.", color="#1B7A43")

    def _open_in_external_editor(self):
        ensure_game_csvs(force_reset=False)
        csv_path = Path(WORD_MATCH_CSV)
        if not csv_path.exists():
            self._save_csv()

        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(csv_path.resolve())))
        if opened:
            self._set_status(f"📂 Opened {csv_path.name} in external editor.", color="#2D6A4F")
        else:
            self._set_status(f"⚠️ Could not open {csv_path} automatically.", color="#C1121F")

    def _generate_missing_audio(self):
        if self._audio_worker is not None and self._audio_worker.isRunning():
            self._set_status("⏳ Audio generation is already running...", color="#2D6A4F")
            return

        rows, err = self._parse_and_validate_editor_csv()
        if err:
            self._set_status(f"❌ Fix CSV before generating audio: {err}", color="#C1121F")
            return

        self.audio_btn.setEnabled(False)
        self._set_status("🔊 Starting background audio synthesis...", color="#2D6A4F")

        worker = _BatchAudioWorker(rows=rows, audio_dir=Path(CUSTOM_AUDIO_DIR), parent=self)
        worker.progress.connect(lambda msg: self._set_status(msg, color="#2D6A4F"))
        worker.finished_batch.connect(self._on_audio_batch_finished)
        worker.finished.connect(worker.deleteLater)
        self._audio_worker = worker
        worker.start()

    def _on_audio_batch_finished(self, generated: int, failed: int):
        self.audio_btn.setEnabled(True)
        self._audio_worker = None
        if failed > 0:
            self._set_status(
                f"⚠️ Generated {generated} audio file(s), {failed} failed.",
                color="#C1121F",
            )
        else:
            self._set_status(
                f"✅ Audio batch complete: {generated} new file(s) generated.",
                color="#1B7A43",
            )


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]} — AddWordPage module loaded.")