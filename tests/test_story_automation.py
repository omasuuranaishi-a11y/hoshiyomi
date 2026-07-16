from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest

from PIL import Image

from backend.story_copy import generate_story_copy
from backend.story_renderer import render_story_images
from backend.story_sky import build_daily_sky, swe


@unittest.skipIf(swe is None, "pyswisseph is not installed")
class StoryAutomationTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["STORY_FONT_DOWNLOAD"] = "false"

    def test_daily_sky_uses_real_positions(self) -> None:
        facts = build_daily_sky("2026-07-16")
        self.assertEqual(facts["target_date"], "2026-07-16")
        self.assertEqual(len(facts["positions"]), 10)
        self.assertIn(facts["moon"]["sign"], [
            "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
            "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座",
        ])
        self.assertGreaterEqual(facts["moon_phase"]["illumination_percent"], 0)
        self.assertLessEqual(facts["moon_phase"]["illumination_percent"], 100)

    def test_offline_copy_and_renderer_create_three_story_images(self) -> None:
        facts = build_daily_sky("2026-07-16")
        copy = generate_story_copy(facts, offline=True)
        self.assertEqual(len(copy.slides), 3)

        with tempfile.TemporaryDirectory() as temporary:
            paths = render_story_images(copy, "2026-07-16", output_root=temporary)
            self.assertEqual(len(paths), 3)
            for path in paths:
                self.assertTrue(Path(path).is_file())
                with Image.open(path) as image:
                    self.assertEqual(image.size, (1080, 1920))
                    self.assertEqual(image.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
