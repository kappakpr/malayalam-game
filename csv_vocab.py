# Malayalam Games — Per-Game CSV Data Loader
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import csv
from pathlib import Path
import shutil
import sys
from typing import Any

from pathlib import Path

USER_DATA_DIR: Path = Path.home() / ".local" / "share" / "malayalam_games"  # or your platformdirs / app path
CSV_DIR = Path(USER_DATA_DIR) / "csv_data"

WORD_MATCH_CSV = CSV_DIR / "word_match.csv"
LETTER_TRACING_CSV = CSV_DIR / "letter_tracing.csv"
WORD_BUILDER_CSV = CSV_DIR / "word_builder.csv"
SCRABBLE_RACKS_CSV = CSV_DIR / "scrabble_racks.csv"

CSV_HEADERS: dict[str, list[str]] = {
    "word_match.csv": ["id", "ml", "en", "emoji", "cat"],
    "letter_tracing.csv": ["id", "char", "translit"],
    "word_builder.csv": ["id", "word", "en", "emoji", "tiles"],
    "scrabble_racks.csv": ["tiles", "bonus_index"],
}


def _resource_path(relative_path: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_dir / relative_path


ASSETS_CSV_DIR = _resource_path("assets/csv")


def _write_header_only(target: Path, filename: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS.get(filename, []))
        writer.writeheader()


def _seed_one_csv(target: Path, filename: str, force: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    source = ASSETS_CSV_DIR / filename

    if force or not target.exists() or target.stat().st_size == 0:
        if source.exists() and source.stat().st_size > 0:
            shutil.copy2(source, target)
        elif not target.exists():
            _write_header_only(target, filename)


def ensure_game_csvs(force_reset: bool = False) -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    _seed_one_csv(WORD_MATCH_CSV, "word_match.csv", force=force_reset)
    _seed_one_csv(LETTER_TRACING_CSV, "letter_tracing.csv", force=force_reset)
    _seed_one_csv(WORD_BUILDER_CSV, "word_builder.csv", force=force_reset)
    _seed_one_csv(SCRABBLE_RACKS_CSV, "scrabble_racks.csv", force=force_reset)


def _parse_tiles(raw_tiles: str) -> list[str]:
    if not raw_tiles:
        return []
    delimiter = "|" if "|" in raw_tiles else ","
    return [t.strip() for t in raw_tiles.split(delimiter) if t.strip()]


def load_word_match_csv() -> list[dict[str, Any]]:
    ensure_game_csvs()
    items: list[dict[str, Any]] = []
    with WORD_MATCH_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            ml = (row.get("ml") or "").strip()
            en = (row.get("en") or "").strip()
            if ml and en:
                items.append({
                    "id": (row.get("id") or en).strip(),
                    "ml": ml,
                    "en": en,
                    "emoji": (row.get("emoji") or "🌟").strip(),
                    "cat": (row.get("cat") or "General").strip(),
                })
    return items


def load_letter_tracing_csv() -> list[dict[str, Any]]:
    ensure_game_csvs()
    letters: list[dict[str, Any]] = []
    with LETTER_TRACING_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            char = (row.get("char") or "").strip()
            if char:
                letters.append({
                    "id": (row.get("id") or "").strip(),
                    "char": char,
                    "translit": (row.get("translit") or "").strip(),
                })
    return letters


def load_word_builder_csv() -> list[dict[str, Any]]:
    ensure_game_csvs()
    puzzles: list[dict[str, Any]] = []
    with WORD_BUILDER_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            word = (row.get("word") or "").strip()
            tiles = _parse_tiles(row.get("tiles") or "")
            if word and tiles:
                puzzles.append({
                    "id": (row.get("id") or word).strip(),
                    "word": word,
                    "en": (row.get("en") or "").strip(),
                    "emoji": (row.get("emoji") or "🧩").strip(),
                    "tiles": tiles,
                })
    return puzzles


def load_scrabble_racks_csv() -> list[dict[str, Any]]:
    ensure_game_csvs()
    racks: list[dict[str, Any]] = []
    with SCRABBLE_RACKS_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            tiles = _parse_tiles(row.get("tiles") or "")
            if not tiles:
                continue
            raw_bonus = (row.get("bonus_index") or "").strip()
            bonus_idx: int | None = None
            if raw_bonus.isdigit():
                parsed_idx = int(raw_bonus)
                if 0 <= parsed_idx < len(tiles):
                    bonus_idx = parsed_idx
            racks.append({"tiles": tiles, "bonus_index": bonus_idx})
    return racks