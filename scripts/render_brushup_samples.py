from __future__ import annotations

from datetime import date
from pathlib import Path

from backend.story_four import build_slot_content, render_slot_story, validate_content_depth


def preview_facts(day: date) -> dict:
    """Stable preview fixture; production continues to use Swiss Ephemeris."""
    return {
        "target_date": day.isoformat(),
        "positions": [
            {"planet": "太陽", "longitude": 142.0},
            {"planet": "月", "longitude": 157.0},
        ],
        "moon": {
            "planet": "月",
            "sign": "乙女座",
            "degree_in_sign": 7.0,
            "longitude": 157.0,
        },
        "moon_phase": {
            "name": "満ちていく三日月期",
            "illumination_percent": 11.8,
        },
        "moon_ingress": None,
        "major_aspects": [
            {"planets": ["月", "金星"], "aspect": "スクエア", "orb": 0.8}
        ],
        "source": "preview fixture only",
    }


def main() -> None:
    day = date(2026, 8, 15)
    facts = preview_facts(day)
    output_dir = Path("generated") / "brushup-samples" / day.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    for slot in ("morning", "night", "evening"):
        content = build_slot_content(facts, slot)
        validate_content_depth(content)
        output_path = output_dir / f"{slot}.jpg"
        render_slot_story(content, day, output_path)
        print(f"{slot}: {output_path} ({output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
