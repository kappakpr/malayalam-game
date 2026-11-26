# Malayalam Games — Batch Audio Generator
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

import argparse
import asyncio
import csv
from pathlib import Path
import sys

import edge_tts

VOICE = "ml-IN-SobhanaNeural"
RATE = "-15%"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = PROJECT_ROOT / "assets" / "audio"
ASSETS_CSV_DIR = PROJECT_ROOT / "assets" / "csv"


def _read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return []
    with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
        return [
            {k.strip(): (v or "").strip() for k, v in row.items() if k}
            for row in csv.DictReader(f)
            if any((v or "").strip() for v in row.values())
        ]


def collect_audio_entries(csv_dir: Path = ASSETS_CSV_DIR) -> dict[str, str]:
    entries: dict[str, str] = {}

    # 1. Word Match entries (also supplies shared vocabulary for Scrabble)
    for row in _read_csv_rows(csv_dir / "word_match.csv"):
        fid = row.get("id", "")
        ml = row.get("ml", "")
        if fid and ml:
            entries[fid] = ml

    # 2. Letter Tracing entries
    for row in _read_csv_rows(csv_dir / "letter_tracing.csv"):
        fid = row.get("id", "")
        char = row.get("char") or row.get("ml") or ""
        if fid and char:
            entries[fid] = char

    # 3. Word Builder entries
    for row in _read_csv_rows(csv_dir / "word_builder.csv"):
        fid = row.get("id", "")
        word = row.get("word") or row.get("ml") or ""
        if fid and word and fid not in entries:
            entries[fid] = word

    return entries


async def _synthesize_one(
    semaphore: asyncio.Semaphore,
    file_id: str,
    text: str,
    out_path: Path,
    overwrite: bool,
    retries: int = 3,
) -> tuple[str, str]:
    if out_path.exists() and out_path.stat().st_size > 0 and not overwrite:
        return ("skipped", file_id)

    tmp_path = out_path.with_suffix(".mp3.part")
    async with semaphore:
        for attempt in range(1, retries + 1):
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
                comm = edge_tts.Communicate(text, VOICE, rate=RATE)
                await comm.save(str(tmp_path))
                if tmp_path.exists() and tmp_path.stat().st_size > 0:
                    tmp_path.replace(out_path)
                    return ("saved", file_id)
                raise RuntimeError("Empty audio file produced")
            except Exception as exc:
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
                if attempt < retries:
                    await asyncio.sleep(0.6 * attempt)
                else:
                    print(f"[Error] {file_id} ({text}): {exc}", file=sys.stderr)
                    return ("failed", file_id)


async def generate_all(
    out_dir: Path = DEFAULT_OUT_DIR,
    csv_dir: Path = ASSETS_CSV_DIR,
    overwrite: bool = False,
    concurrency: int = 4,
) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = collect_audio_entries(csv_dir=csv_dir)
    sem = asyncio.Semaphore(max(1, concurrency))

    tasks = [
        _synthesize_one(sem, fid, text, out_dir / f"{fid}.mp3", overwrite=overwrite)
        for fid, text in entries.items()
    ]
    results = await asyncio.gather(*tasks)

    counts = {"saved": 0, "skipped": 0, "failed": 0}
    for status, fid in results:
        counts[status] = counts.get(status, 0) + 1
        if status == "saved":
            print(f"Saved {fid}.mp3")
        elif status == "skipped":
            print(f"Skipping {fid}.mp3 (already exists)")

    print(
        f"Summary: {counts['saved']} saved, {counts['skipped']} skipped, {counts['failed']} failed."
    )
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Malayalam TTS MP3 assets from CSV files.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate MP3 files even if a non-empty file already exists.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Maximum concurrent edge-tts requests (default: 4).",
    )
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=ASSETS_CSV_DIR,
        help="Directory containing game CSV files (default: assets/csv).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for MP3 files (default: assets/audio).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    counts = asyncio.run(
        generate_all(
            out_dir=args.out_dir,
            csv_dir=args.csv_dir,
            overwrite=args.overwrite,
            concurrency=args.concurrency,
        )
    )
    return 1 if counts.get("failed", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())