# Malayalam Games — CSV & Audio Asset Validator
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

from collections import Counter
import csv
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
CSV_DIR = PROJECT_ROOT / "assets" / "csv"
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"


def _parse_tiles(raw: str) -> list[str]:
    if not raw:
        return []
    delim = "|" if "|" in raw else ","
    return [t.strip() for t in raw.split(delim) if t.strip()]


def _can_spell_from_tiles(word: str, tiles: list[str]) -> bool:
    if not word or not tiles:
        return False
    # Greedy match preferring longer tile chunks first (handles conjuncts/vowel signs)
    sorted_tiles = sorted(set(tiles), key=len, reverse=True)
    counts = Counter(tiles)

    def _backtrack(pos: int) -> bool:
        if pos == len(word):
            return True
        for tile in sorted_tiles:
            if counts[tile] > 0 and word.startswith(tile, pos):
                counts[tile] -= 1
                if _backtrack(pos + len(tile)):
                    return True
                counts[tile] += 1
        return False

    return _backtrack(0)


def validate() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    audio_ids_needed: set[str] = set()

    required_files = {
        "word_match.csv": ["id", "ml", "en", "emoji", "cat"],
        "letter_tracing.csv": ["id", "char", "translit"],
        "word_builder.csv": ["id", "word", "en", "emoji", "tiles"],
        "scrabble_racks.csv": ["tiles", "bonus_index"],
    }

    for fname, cols in required_files.items():
        path = CSV_DIR / fname
        if not path.exists():
            errors.append(f"Missing CSV file: {path}")
            continue
        with path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            missing_cols = [c for c in cols if c not in fieldnames]
            if missing_cols:
                errors.append(f"{fname} missing columns: {missing_cols}")
                continue
            rows = list(reader)

        if fname == "word_match.csv":
            for i, r in enumerate(rows, start=2):
                aid = (r.get("id") or "").strip()
                ml = (r.get("ml") or "").strip()
                en = (r.get("en") or "").strip()
                if not ml or not en:
                    errors.append(f"{fname}:{i} missing ml or en")
                if aid:
                    audio_ids_needed.add(aid)

        elif fname == "letter_tracing.csv":
            for i, r in enumerate(rows, start=2):
                aid = (r.get("id") or "").strip()
                ch = (r.get("char") or "").strip()
                if not ch:
                    errors.append(f"{fname}:{i} missing char")
                if aid:
                    audio_ids_needed.add(aid)

        elif fname == "word_builder.csv":
            for i, r in enumerate(rows, start=2):
                aid = (r.get("id") or "").strip()
                word = (r.get("word") or "").strip()
                tiles = _parse_tiles(r.get("tiles") or "")
                if not word or not tiles:
                    errors.append(f"{fname}:{i} missing word or tiles")
                    continue
                if not _can_spell_from_tiles(word, tiles):
                    warnings.append(
                        f"{fname}:{i} word '{word}' may not assemble cleanly from tiles {tiles}"
                    )
                if aid:
                    audio_ids_needed.add(aid)

        elif fname == "scrabble_racks.csv":
            for i, r in enumerate(rows, start=2):
                tiles = _parse_tiles(r.get("tiles") or "")
                if not tiles:
                    errors.append(f"{fname}:{i} empty tiles rack")
                    continue
                raw_bonus = (r.get("bonus_index") or "").strip()
                if raw_bonus:
                    if not raw_bonus.isdigit() or not (0 <= int(raw_bonus) < len(tiles)):
                        warnings.append(
                            f"{fname}:{i} bonus_index '{raw_bonus}' out of range for {len(tiles)} tiles"
                        )

    for aid in sorted(audio_ids_needed):
        mp3 = AUDIO_DIR / f"{aid}.mp3"
        if not mp3.exists() or mp3.stat().st_size == 0:
            warnings.append(f"Missing audio file: assets/audio/{aid}.mp3")

    for w in warnings:
        print(f"[WARN] {w}")
    for e in errors:
        print(f"[ERROR] {e}", file=sys.stderr)

    print(
        f"Validation complete: {len(errors)} error(s), {len(warnings)} warning(s), "
        f"{len(audio_ids_needed)} audio IDs checked."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(validate())