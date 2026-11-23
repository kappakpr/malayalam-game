import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def get_user_data_dir(app_name: str = "MalayalamGame") -> Path:
    """Return the cross-platform application support / data directory."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
        return base / app_name
    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data) if xdg_data else (Path.home() / ".local" / "share")
    return base / app_name


USER_DATA_DIR: Path = get_user_data_dir("MalayalamGame")
CUSTOM_AUDIO_DIR: Path = USER_DATA_DIR / "custom_audio"
CUSTOM_VOCAB_PATH: Path = USER_DATA_DIR / "custom_vocab.json"


def slugify_id(text: str) -> str:
    """Convert arbitrary text (English, phrases, or fallback) into a safe audio/item ID."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return cleaned or "custom_word"


def load_custom_vocab() -> list[dict[str, Any]]:
    """Load saved custom vocabulary entries from disk."""
    if not CUSTOM_VOCAB_PATH.exists():
        return []

    try:
        raw_text = CUSTOM_VOCAB_PATH.read_text(encoding="utf-8").strip()
        if not raw_text:
            return []
        data = json.loads(raw_text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[Custom Vocab Load Error] {exc}")
        return []

    if not isinstance(data, list):
        return []

    valid_items: list[dict[str, Any]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        ml = str(entry.get("ml", "")).strip()
        en = str(entry.get("en", "")).strip()
        if not ml or not en:
            continue
        item_id = str(entry.get("id", "")).strip() or slugify_id(en)
        emoji = str(entry.get("emoji", "")).strip() or "🌟"
        cat = str(entry.get("cat", "")).strip() or "Custom"
        valid_items.append(
            {
                "id": item_id,
                "ml": ml,
                "en": en,
                "emoji": emoji,
                "cat": cat,
            }
        )

    return valid_items


def save_custom_vocab(items: list[dict[str, Any]]) -> bool:
    """Persist custom vocabulary entries to custom_vocab.json."""
    try:
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        CUSTOM_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = CUSTOM_VOCAB_PATH.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp_path, CUSTOM_VOCAB_PATH)
        return True
    except OSError as exc:
        print(f"[Custom Vocab Save Error] {exc}")
        return False