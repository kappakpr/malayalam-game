import asyncio
from pathlib import Path
import edge_tts
from vocab_data import VOCAB_ITEMS, TRACE_LETTERS

VOICE = "ml-IN-SobhanaNeural"
RATE = "-15%"


async def main(overwrite: bool = False):
    out_dir = Path("assets/audio")
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_entries = {item["id"]: item["ml"] for item in VOCAB_ITEMS}
    audio_entries.update({letter["id"]: letter["char"] for letter in TRACE_LETTERS})

    for file_id, text in audio_entries.items():
        out_path = out_dir / f"{file_id}.mp3"
        if out_path.exists() and out_path.stat().st_size > 0 and not overwrite:
            print(f"Skipping {file_id}.mp3 (already exists)")
            continue
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(str(out_path))
        print(f"Saved {file_id}.mp3")


if __name__ == "__main__":
    asyncio.run(main())