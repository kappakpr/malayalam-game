import random
from pathlib import Path
import unittest

VOCABULARY = [
    {"ml": "അമ്മ", "en": "Mother", "emoji": "👩", "audio": "assets/audio/amma.mp3"},
    {"ml": "ആന", "en": "Elephant", "emoji": "🐘", "audio": "assets/audio/aana.mp3"},
    {"ml": "പൂച്ച", "en": "Cat", "emoji": "🐱", "audio": "assets/audio/poocha.mp3"},
    {"ml": "മരം", "en": "Tree", "emoji": "🌳", "audio": "assets/audio/maram.mp3"},
]


def pick_round_choices(vocab, count=4):
    choices = random.sample(vocab, count)
    target = random.choice(choices)
    return choices, target


class TestMalayalamGameLogic(unittest.TestCase):
    def test_round_choices_has_four_unique_items_and_valid_target(self):
        choices, target = pick_round_choices(VOCABULARY, 4)
        self.assertEqual(len(choices), 4)
        self.assertEqual(len({item["ml"] for item in choices}), 4)
        self.assertIn(target, choices)

    def test_audio_script_exists(self):
        self.assertTrue(Path("generate_audio.py").exists())


if __name__ == "__main__":
    unittest.main()