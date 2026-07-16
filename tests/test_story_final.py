from __future__ import annotations

import os
import tempfile
import unittest

from PIL import Image, ImageDraw

from backend.story_copy import generate_story_copy
from backend.story_renderer import resolve_font_path
from backend.story_renderer_final import _fit_lines, render_story_images
from backend.story_sky import swe
from backend.story_sky_daily import PERSONAL_PLANETS, build_daily_sky


@unittest.skipIf(swe is None, "pysweph is not installed")
class FinalStoryTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["STORY_FONT_DOWNLOAD"] = "false"

    def test_daily_aspect_prioritizes_a_fast_planet(self) -> None:
        facts = build_daily_sky("2026-07-17")
        self.assertTrue(facts["major_aspects"])
        first_planets = set(facts["major_aspects"][0]["planets"])
        self.assertTrue(first_planets.intersection(PERSONAL_PLANETS))

    def test_title_and_action_avoid_single_character_orphans(self) -> None:
        canvas = Image.new("RGB", (1080, 1920), "white")
        draw = ImageDraw.Draw(canvas)
        font_path = resolve_font_path()
        _, title_lines = _fit_lines(
            draw,
            "天王星と海王星が響く日",
            font_path,
            start_size=76,
            minimum_size=54,
            max_width=820,
            max_lines=2,
        )
        _, action_lines = _fit_lines(
            draw,
            "まずは、いまの気分に名前をつけてみる",
            font_path,
            start_size=40,
            minimum_size=30,
            max_width=720,
            max_lines=2,
        )
        self.assertNotEqual(len(title_lines[-1]), 1)
        self.assertNotEqual(len(action_lines[-1]), 1)

    def test_final_renderer_outputs_three_jpegs(self) -> None:
        facts = build_daily_sky("2026-07-17")
        copy = generate_story_copy(facts, offline=True)
        with tempfile.TemporaryDirectory() as temporary:
            paths = render_story_images(copy, "2026-07-17", output_root=temporary)
            self.assertEqual(len(paths), 3)
            for path in paths:
                with Image.open(path) as image:
                    self.assertEqual(image.size, (1080, 1920))
                    self.assertEqual(image.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
