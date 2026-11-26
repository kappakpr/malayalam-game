# Malayalam Games — Vocabulary & CSV Smoke Test
# Game Concept by "Kududu & Kukudu"
# Copyright (C) 2026 Kududu & Kukudu
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import csv_vocab  # noqa: E402
import custom_vocab  # noqa: E402
from custom_vocab import load_custom_vocab, save_custom_vocab  # noqa: E402


def _run_validator(csv_dir: Path) -> subprocess.CompletedProcess[str]:
    validator_path = PROJECT_ROOT / "validate_csv.py"
    return subprocess.run(
        [sys.executable, str(validator_path), "--csv-dir", str(csv_dir)],
        capture_output=True,
        text=True,
        check=False,
    )


def _build_scrabble_lookup(vocab_items: list[dict]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for item in vocab_items:
        ml = (item.get("ml") or "").strip()
        if len(ml) >= 2 and ml not in lookup:
            lookup[ml] = {
                "id": (item.get("id") or "").strip(),
                "en": (item.get("en") or "").strip(),
            }
    return lookup


def _is_valid_vocab_item(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    return bool((item.get("ml") or "").strip()) and bool((item.get("en") or "").strip())


def test_bundled_csv_validation() -> None:
    bundled_dir = PROJECT_ROOT / "assets" / "csv"
    assert bundled_dir.exists(), f"Missing bundled CSV directory: {bundled_dir}"
    res = _run_validator(bundled_dir)
    assert res.returncode == 0, f"Bundled CSV validation failed:\n{res.stdout}\n{res.stderr}"
    print("[PASS] Bundled assets/csv passed validate_csv.py")


def test_validator_catches_invalid_csv() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bad_dir = Path(tmp) / "bad_csv"
        shutil.copytree(PROJECT_ROOT / "assets" / "csv", bad_dir)
        (bad_dir / "word_match.csv").write_text(
            "id,ml\nonly_two_cols,അമ്മ\n",
            encoding="utf-8-sig",
        )
        res = _run_validator(bad_dir)
        assert res.returncode != 0, (
            "Expected non-zero exit code for malformed word_match.csv "
            f"(got {res.returncode}).\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )
        print("[PASS] validate_csv.py flagged malformed word_match.csv")


def test_seeding_reset_and_shared_vocab() -> None:
    orig_csv_dir = csv_vocab.CSV_DIR
    orig_word_match = csv_vocab.WORD_MATCH_CSV
    orig_letter_tracing = csv_vocab.LETTER_TRACING_CSV
    orig_word_builder = csv_vocab.WORD_BUILDER_CSV
    orig_scrabble_racks = csv_vocab.SCRABBLE_RACKS_CSV
    orig_assets_csv_dir = csv_vocab.ASSETS_CSV_DIR

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        seeded_assets = tmp_path / "assets_csv"
        user_csv_dir = tmp_path / "user_csv_data"
        shutil.copytree(PROJECT_ROOT / "assets" / "csv", seeded_assets)

        try:
            csv_vocab.ASSETS_CSV_DIR = seeded_assets
            csv_vocab.CSV_DIR = user_csv_dir
            csv_vocab.WORD_MATCH_CSV = user_csv_dir / "word_match.csv"
            csv_vocab.LETTER_TRACING_CSV = user_csv_dir / "letter_tracing.csv"
            csv_vocab.WORD_BUILDER_CSV = user_csv_dir / "word_builder.csv"
            csv_vocab.SCRABBLE_RACKS_CSV = user_csv_dir / "scrabble_racks.csv"

            # 1. Initial seed
            csv_vocab.ensure_game_csvs(force_reset=False)
            assert csv_vocab.WORD_MATCH_CSV.exists(), "word_match.csv was not seeded"
            assert not (user_csv_dir / "scrabble_words.csv").exists(), (
                "Deprecated scrabble_words.csv should not be created"
            )

            # 2. Modify user CSV and verify force_reset restores bundled template
            bundled_match_text = csv_vocab.WORD_MATCH_CSV.read_text(encoding="utf-8-sig")
            csv_vocab.WORD_MATCH_CSV.write_text(
                "id,ml,en,emoji,cat\ntemp_word,പരീക്ഷ,Test,🧪,Practice\n",
                encoding="utf-8-sig",
            )
            assert "പരീക്ഷ" in csv_vocab.WORD_MATCH_CSV.read_text(encoding="utf-8-sig")

            csv_vocab.ensure_game_csvs(force_reset=True)
            restored_text = csv_vocab.WORD_MATCH_CSV.read_text(encoding="utf-8-sig")
            assert restored_text == bundled_match_text, "force_reset did not restore bundled CSV"
            print("[PASS] Initial seeding and force_reset restored bundled CSV")

            # 3. Verify shared vocabulary powers both Match items and Scrabble lookup
            match_items = csv_vocab.load_word_match_csv()
            assert len(match_items) > 0, "Expected non-empty word_match items"

            scrabble_lookup = _build_scrabble_lookup(match_items)
            sample_item = next(
                (item for item in match_items if len((item.get("ml") or "").strip()) >= 2),
                None,
            )
            assert sample_item is not None, "Expected at least one word with length >= 2"
            assert sample_item["ml"] in scrabble_lookup, (
                f"Match word {sample_item['ml']!r} missing from Scrabble lookup"
            )
            assert scrabble_lookup[sample_item["ml"]]["id"] == sample_item["id"]
            print(
                f"[PASS] Shared vocabulary verified ({len(match_items)} match items, "
                f"{len(scrabble_lookup)} Scrabble words)"
            )
        finally:
            csv_vocab.ASSETS_CSV_DIR = orig_assets_csv_dir
            csv_vocab.CSV_DIR = orig_csv_dir
            csv_vocab.WORD_MATCH_CSV = orig_word_match
            csv_vocab.LETTER_TRACING_CSV = orig_letter_tracing
            csv_vocab.WORD_BUILDER_CSV = orig_word_builder
            csv_vocab.SCRABBLE_RACKS_CSV = orig_scrabble_racks


def test_custom_vocab_merges_into_shared_pool() -> None:
    orig_csv_dir = csv_vocab.CSV_DIR
    orig_word_match = csv_vocab.WORD_MATCH_CSV
    orig_letter_tracing = csv_vocab.LETTER_TRACING_CSV
    orig_word_builder = csv_vocab.WORD_BUILDER_CSV
    orig_scrabble_racks = csv_vocab.SCRABBLE_RACKS_CSV
    orig_assets_csv_dir = csv_vocab.ASSETS_CSV_DIR

    snapshot_custom = load_custom_vocab()
    test_id = "smoke_test_custom_pusthakam"
    initial_entry = {
        "id": test_id,
        "ml": "പുസ്തകം",
        "en": "Book",
        "emoji": "📖",
        "cat": "SmokeTest",
    }
    override_entry = {
        "id": test_id,
        "ml": "പുസ്തകങ്ങൾ",
        "en": "Books",
        "emoji": "📚",
        "cat": "SmokeTest",
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        seeded_assets = tmp_path / "assets_csv"
        user_csv_dir = tmp_path / "user_csv_data"
        shutil.copytree(PROJECT_ROOT / "assets" / "csv", seeded_assets)

        try:
            csv_vocab.ASSETS_CSV_DIR = seeded_assets
            csv_vocab.CSV_DIR = user_csv_dir
            csv_vocab.WORD_MATCH_CSV = user_csv_dir / "word_match.csv"
            csv_vocab.LETTER_TRACING_CSV = user_csv_dir / "letter_tracing.csv"
            csv_vocab.WORD_BUILDER_CSV = user_csv_dir / "word_builder.csv"
            csv_vocab.SCRABBLE_RACKS_CSV = user_csv_dir / "scrabble_racks.csv"

            csv_vocab.ensure_game_csvs(force_reset=False)
            base_custom = [w for w in snapshot_custom if w.get("id") != test_id]
            save_custom_vocab(base_custom + [initial_entry])

            reloaded_custom = load_custom_vocab()
            assert any(w.get("id") == test_id for w in reloaded_custom), (
                "Custom test entry was not persisted by save_custom_vocab"
            )

            match_items = csv_vocab.load_word_match_csv()
            combined_pool = match_items + reloaded_custom
            assert any(
                item.get("ml") == "പുസ്തകം" and item.get("cat") == "SmokeTest"
                for item in combined_pool
            ), "Custom entry missing from combined Match vocabulary pool"

            scrabble_lookup = _build_scrabble_lookup(combined_pool)
            assert "പുസ്തകം" in scrabble_lookup, "Custom entry missing from Scrabble lookup"
            assert scrabble_lookup["പുസ്തകം"]["id"] == test_id
            assert scrabble_lookup["പുസ്തകം"]["en"] == "Book"

            # Override existing custom id and confirm duplicate is replaced cleanly
            deduped_custom = [w for w in load_custom_vocab() if w.get("id") != test_id]
            save_custom_vocab(deduped_custom + [override_entry])

            after_override_custom = load_custom_vocab()
            matching_ids = [w for w in after_override_custom if w.get("id") == test_id]
            assert len(matching_ids) == 1, f"Expected 1 entry for {test_id!r}, got {len(matching_ids)}"
            assert matching_ids[0]["ml"] == "പുസ്തകങ്ങൾ"
            assert matching_ids[0]["en"] == "Books"

            updated_pool = match_items + after_override_custom
            assert not any(
                item.get("id") == test_id and item.get("ml") == "പുസ്തകം"
                for item in updated_pool
            ), "Stale custom entry remained after id override"
            assert any(
                item.get("id") == test_id and item.get("ml") == "പുസ്തകങ്ങൾ"
                for item in updated_pool
            ), "Updated custom entry missing from combined pool"

            updated_lookup = _build_scrabble_lookup(updated_pool)
            assert "പുസ്തകങ്ങൾ" in updated_lookup
            assert updated_lookup["പുസ്തകങ്ങൾ"]["id"] == test_id
            assert updated_lookup["പുസ്തകങ്ങൾ"]["en"] == "Books"

            # Collision check: custom entry shares an id with an existing word_match.csv row
            csv_anchor = next(
                (item for item in match_items if (item.get("id") or "").strip()),
                None,
            )
            assert csv_anchor is not None, "Expected at least one word_match.csv item with an id"
            shared_id = csv_anchor["id"].strip()
            collision_ml = "വിദ്യാലയം"
            collision_entry = {
                "id": shared_id,
                "ml": collision_ml,
                "en": "School Override",
                "emoji": "🏫",
                "cat": "CollisionTest",
            }
            save_custom_vocab(
                [w for w in load_custom_vocab() if w.get("id") != shared_id] + [collision_entry]
            )
            collision_custom = load_custom_vocab()
            collision_pool = match_items + collision_custom

            shared_id_entries = [item for item in collision_pool if item.get("id") == shared_id]
            assert len(shared_id_entries) >= 2, (
                f"Expected both CSV row and custom row with shared id {shared_id!r} in combined pool"
            )
            assert any(item.get("ml") == collision_ml for item in collision_pool), (
                "Custom collision entry missing from combined pool"
            )

            collision_lookup = _build_scrabble_lookup(collision_pool)
            if len(collision_ml) >= 2 and collision_ml != (csv_anchor.get("ml") or "").strip():
                assert collision_ml in collision_lookup, (
                    "Distinct custom word with shared id should still be reachable by Malayalam text in Scrabble"
                )
                assert collision_lookup[collision_ml]["id"] == shared_id
                assert collision_lookup[collision_ml]["en"] == "School Override"

            print(
                "[PASS] load_custom_vocab() merges, overrides duplicate IDs, and handles word_match.csv id collisions"
            )
        finally:
            save_custom_vocab(snapshot_custom)
            csv_vocab.ASSETS_CSV_DIR = orig_assets_csv_dir
            csv_vocab.CSV_DIR = orig_csv_dir
            csv_vocab.WORD_MATCH_CSV = orig_word_match
            csv_vocab.LETTER_TRACING_CSV = orig_letter_tracing
            csv_vocab.WORD_BUILDER_CSV = orig_word_builder
            csv_vocab.SCRABBLE_RACKS_CSV = orig_scrabble_racks


def test_custom_vocab_skips_blank_or_malformed_entries() -> None:
    orig_csv_dir = csv_vocab.CSV_DIR
    orig_word_match = csv_vocab.WORD_MATCH_CSV
    orig_letter_tracing = csv_vocab.LETTER_TRACING_CSV
    orig_word_builder = csv_vocab.WORD_BUILDER_CSV
    orig_scrabble_racks = csv_vocab.SCRABBLE_RACKS_CSV
    orig_assets_csv_dir = csv_vocab.ASSETS_CSV_DIR

    snapshot_custom = load_custom_vocab()
    valid_id = "smoke_test_valid_entry"
    valid_entry = {
        "id": valid_id,
        "ml": "വെള്ളം",
        "en": "Water",
        "emoji": "💧",
        "cat": "MalformedTest",
    }
    blank_and_malformed = [
        {},
        {"id": "blank_fields", "ml": "   ", "en": ""},
        {"id": "missing_en", "ml": "സൂര്യൻ"},
        {"id": "missing_ml", "en": "Sun"},
        "not_a_dict",
        123,
    ]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        seeded_assets = tmp_path / "assets_csv"
        user_csv_dir = tmp_path / "user_csv_data"
        shutil.copytree(PROJECT_ROOT / "assets" / "csv", seeded_assets)

        try:
            csv_vocab.ASSETS_CSV_DIR = seeded_assets
            csv_vocab.CSV_DIR = user_csv_dir
            csv_vocab.WORD_MATCH_CSV = user_csv_dir / "word_match.csv"
            csv_vocab.LETTER_TRACING_CSV = user_csv_dir / "letter_tracing.csv"
            csv_vocab.WORD_BUILDER_CSV = user_csv_dir / "word_builder.csv"
            csv_vocab.SCRABBLE_RACKS_CSV = user_csv_dir / "scrabble_racks.csv"
            csv_vocab.ensure_game_csvs(force_reset=False)

            base_custom = [w for w in snapshot_custom if w.get("id") != valid_id]
            save_custom_vocab(base_custom + blank_and_malformed + [valid_entry])  # type: ignore[list-item]

            loaded = load_custom_vocab()
            assert isinstance(loaded, list)
            assert any(w.get("id") == valid_id and w.get("ml") == "വെള്ളം" for w in loaded), (
                "Valid custom entry should survive alongside malformed entries"
            )
            assert not any(
                not (w.get("ml") or "").strip() or not (w.get("en") or "").strip()
                for w in loaded
                if isinstance(w, dict)
            ), "Blank or incomplete custom entries should not be returned as valid items"

            match_items = csv_vocab.load_word_match_csv()
            filtered_loaded = [w for w in loaded if _is_valid_vocab_item(w)]
            combined_pool = match_items + filtered_loaded
            lookup = _build_scrabble_lookup(combined_pool)
            assert "വെള്ളം" in lookup
            assert "" not in lookup

            # If custom_vocab exposes a file path attribute, verify corrupt/non-list JSON is handled safely
            custom_file_attr = next(
                (
                    getattr(custom_vocab, attr)
                    for attr in ("CUSTOM_VOCAB_FILE", "CUSTOM_VOCAB_PATH", "VOCAB_FILE")
                    if hasattr(custom_vocab, attr) and isinstance(getattr(custom_vocab, attr), Path)
                ),
                None,
            )
            if custom_file_attr is not None:
                orig_bytes = custom_file_attr.read_bytes() if custom_file_attr.exists() else None
                try:
                    custom_file_attr.write_text("{not valid json", encoding="utf-8")
                    corrupt_loaded = load_custom_vocab()
                    assert isinstance(corrupt_loaded, list)

                    custom_file_attr.write_text(json.dumps({"unexpected": "object"}), encoding="utf-8")
                    non_list_loaded = load_custom_vocab()
                    assert isinstance(non_list_loaded, list)
                finally:
                    if orig_bytes is not None:
                        custom_file_attr.write_bytes(orig_bytes)
                    elif custom_file_attr.exists():
                        custom_file_attr.unlink()

            print("[PASS] load_custom_vocab() safely skips blank or malformed entries")
        finally:
            save_custom_vocab(snapshot_custom)
            csv_vocab.ASSETS_CSV_DIR = orig_assets_csv_dir
            csv_vocab.CSV_DIR = orig_csv_dir
            csv_vocab.WORD_MATCH_CSV = orig_word_match
            csv_vocab.LETTER_TRACING_CSV = orig_letter_tracing
            csv_vocab.WORD_BUILDER_CSV = orig_word_builder
            csv_vocab.SCRABBLE_RACKS_CSV = orig_scrabble_racks


def test_whitespace_trimming_in_vocab_fields() -> None:
    orig_csv_dir = csv_vocab.CSV_DIR
    orig_word_match = csv_vocab.WORD_MATCH_CSV
    orig_letter_tracing = csv_vocab.LETTER_TRACING_CSV
    orig_word_builder = csv_vocab.WORD_BUILDER_CSV
    orig_scrabble_racks = csv_vocab.SCRABBLE_RACKS_CSV
    orig_assets_csv_dir = csv_vocab.ASSETS_CSV_DIR

    snapshot_custom = load_custom_vocab()
    clean_id = "smoke_test_trimmed_kadal"
    padded_entry = {
        "id": f"  {clean_id}\t",
        "ml": " \n കടൽ  ",
        "en": "  Sea \t ",
        "emoji": "🌊",
        "cat": "  WhitespaceTest  ",
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        seeded_assets = tmp_path / "assets_csv"
        user_csv_dir = tmp_path / "user_csv_data"
        shutil.copytree(PROJECT_ROOT / "assets" / "csv", seeded_assets)

        try:
            csv_vocab.ASSETS_CSV_DIR = seeded_assets
            csv_vocab.CSV_DIR = user_csv_dir
            csv_vocab.WORD_MATCH_CSV = user_csv_dir / "word_match.csv"
            csv_vocab.LETTER_TRACING_CSV = user_csv_dir / "letter_tracing.csv"
            csv_vocab.WORD_BUILDER_CSV = user_csv_dir / "word_builder.csv"
            csv_vocab.SCRABBLE_RACKS_CSV = user_csv_dir / "scrabble_racks.csv"
            csv_vocab.ensure_game_csvs(force_reset=False)

            base_custom = [
                w for w in snapshot_custom
                if (w.get("id") or "").strip() != clean_id
            ]
            save_custom_vocab(base_custom + [padded_entry])

            loaded = load_custom_vocab()
            matched = next(
                (w for w in loaded if (w.get("id") or "").strip() == clean_id),
                None,
            )
            assert matched is not None, "Padded custom entry was not found after reload"

            trimmed_id = (matched.get("id") or "").strip()
            trimmed_ml = (matched.get("ml") or "").strip()
            trimmed_en = (matched.get("en") or "").strip()

            assert trimmed_id == clean_id, f"Expected trimmed id {clean_id!r}, got {trimmed_id!r}"
            assert trimmed_ml == "കടൽ", f"Expected trimmed ml 'കടൽ', got {trimmed_ml!r}"
            assert trimmed_en == "Sea", f"Expected trimmed en 'Sea', got {trimmed_en!r}"

            combined_pool = csv_vocab.load_word_match_csv() + loaded
            assert any(
                (item.get("ml") or "").strip() == "കടൽ"
                and (item.get("id") or "").strip() == clean_id
                for item in combined_pool
            ), "Trimmed entry missing from combined Match vocabulary pool"

            lookup = _build_scrabble_lookup(combined_pool)
            assert "കടൽ" in lookup, "Trimmed Malayalam word missing from Scrabble lookup"
            assert "  കടൽ  " not in lookup, "Un-trimmed Malayalam key should not appear in lookup"
            assert lookup["കടൽ"]["id"] == clean_id
            assert lookup["കടൽ"]["en"] == "Sea"

            print("[PASS] Leading/trailing whitespace in ml, en, and id is trimmed cleanly")
        finally:
            save_custom_vocab(snapshot_custom)
            csv_vocab.ASSETS_CSV_DIR = orig_assets_csv_dir
            csv_vocab.CSV_DIR = orig_csv_dir
            csv_vocab.WORD_MATCH_CSV = orig_word_match
            csv_vocab.LETTER_TRACING_CSV = orig_letter_tracing
            csv_vocab.WORD_BUILDER_CSV = orig_word_builder
            csv_vocab.SCRABBLE_RACKS_CSV = orig_scrabble_racks


def main() -> int:
    test_bundled_csv_validation()
    test_validator_catches_invalid_csv()
    test_seeding_reset_and_shared_vocab()
    test_custom_vocab_merges_into_shared_pool()
    test_custom_vocab_skips_blank_or_malformed_entries()
    test_whitespace_trimming_in_vocab_fields()
    print("All vocabulary smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())