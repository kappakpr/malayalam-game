# Malayalam Games — Audio Synthesis, Caching & Playback Manager
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

import asyncio
from pathlib import Path
import sys

import edge_tts
from PySide6.QtCore import QObject, QThread, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from custom_vocab import CUSTOM_AUDIO_DIR, USER_DATA_DIR, slugify_id


def _resource_path(relative_path: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_dir / relative_path


AUDIO_DIR = _resource_path("assets/audio")
CACHE_AUDIO_DIR = USER_DATA_DIR / "cache"


class PhraseSpeakWorker(QThread):
    ready_to_play = Signal(str)

    def __init__(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        cache_stem: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.text = text
        self.voice = voice
        self.rate = rate
        self.cache_stem = cache_stem

    def run(self):
        try:
            CACHE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            safe_name = slugify_id(self.cache_stem or f"{self.voice}_{self.text}")
            out_path = CACHE_AUDIO_DIR / f"{safe_name}.mp3"

            async def _gen():
                comm = edge_tts.Communicate(self.text, self.voice, rate=self.rate)
                await comm.save(str(out_path))

            asyncio.run(_gen())
            if out_path.exists() and out_path.stat().st_size > 0:
                self.ready_to_play.emit(str(out_path.resolve()))
        except Exception as exc:
            print(f"[TTS Error] {exc}")


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


class AudioManager(QObject):
    """Owns Qt media playback, TTS fallback workers, and active thread lifecycle."""

    def __init__(self, window, parent=None):
        super().__init__(parent or window)
        self.window = window
        self._active_workers: list[QThread] = []
        self._pending_followup_phrase: tuple[str, str] | None = None
        self._followup_triggered = False

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.9)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self._on_audio_error)
        self.player.positionChanged.connect(self._on_audio_position_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def register_worker(self, worker: QThread, on_ready=None):
        self._active_workers.append(worker)
        if on_ready is not None and hasattr(worker, "ready_to_play"):
            worker.ready_to_play.connect(on_ready)
        worker.finished.connect(lambda w=worker: self._release_worker(w))
        worker.start()

    def _release_worker(self, worker: QThread):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        worker.deleteLater()

    def shutdown(self):
        for worker in list(self._active_workers):
            if worker.isRunning():
                worker.quit()
                worker.wait(1500)

    def _on_audio_error(self, error, error_string: str):
        print(f"[Audio Error] {error}: {error_string}")

    def _resolve_malayalam_text_for_audio_id(self, file_id: str) -> str:
        if not file_id:
            return ""
        for item in getattr(self.window, "vocab_items", []):
            if item.get("id") == file_id and item.get("ml"):
                return str(item["ml"]).strip()
        for puzzle in getattr(self.window, "word_puzzles", []):
            if puzzle.get("id") == file_id:
                word = puzzle.get("word") or puzzle.get("ml") or ""
                if word:
                    return str(word).strip()
        return ""

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
        if mp3_path:
            self._play_local_mp3(mp3_path)
            return

        ml_text = self._resolve_malayalam_text_for_audio_id(file_id)
        if ml_text:
            cache_stem = f"ml_{slugify_id(file_id)}"
            cached_ml = CACHE_AUDIO_DIR / f"{slugify_id(cache_stem)}.mp3"
            print(f"[TTS Fallback] id={file_id!r} text={ml_text!r} cached={cached_ml.exists()}")
            if cached_ml.exists() and cached_ml.stat().st_size > 0:
                self._play_local_mp3(str(cached_ml.resolve()))
                return
            worker = PhraseSpeakWorker(
                ml_text,
                voice="ml-IN-SobhanaNeural",
                rate="-15%",
                cache_stem=cache_stem,
                parent=self,
            )
            self.register_worker(worker, on_ready=self._play_local_mp3)
            return

        print(f"[TTS Fallback] id={file_id!r} text='' (no matching Malayalam text)")
        if self._pending_followup_phrase:
            phrase, voice = self._pending_followup_phrase
            self._pending_followup_phrase = None
            self.say_phrase(phrase, voice=voice)

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

        worker = PhraseSpeakWorker(text, voice=voice, parent=self)
        self.register_worker(worker, on_ready=self._play_local_mp3 if play_immediately else None)

    def _play_local_mp3(self, mp3_path: str):
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(mp3_path))
        self.player.play()