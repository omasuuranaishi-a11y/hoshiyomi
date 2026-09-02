from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from backend.story_four import (
    TAROT_POSTS,
    TAROT_REFRESH_DATE,
    build_slot_content,
    render_slot_story,
    validate_content_depth,
)
from backend.story_quality import validate_story_asset


def preview_facts(day: date) -> dict:
    """Stable visual fixture; production continues to use daily sky facts."""
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
    output_dir = Path("samples") / "tarot-refresh-v13"
    rotation_dir = output_dir / "rotation-check"
    rotation_dir.mkdir(parents=True, exist_ok=True)
    sample_indexes = {
        0: "01-comparison.jpg",
        1: "02-daily.jpg",
        3: "03-symbol.jpg",
        6: "04-choice.jpg",
        2: "05-three-card-spread.jpg",
    }
    for index in range(len(TAROT_POSTS)):
        day = TAROT_REFRESH_DATE + timedelta(days=index)
        content = build_slot_content(preview_facts(day), "evening")
        depth_report = validate_content_depth(content)
        if not depth_report["passed"]:
            raise RuntimeError(f"copy validation failed: {content['post_key']}")
        rotation_path = rotation_dir / f"{index:02d}-{content['post_key']}.jpg"
        render_slot_story(content, day, rotation_path)
        asset_report = validate_story_asset(rotation_path, content, day)
        if not asset_report["passed"]:
            raise RuntimeError(f"asset validation failed: {content['post_key']}")
        if index in sample_indexes:
            sample_path = output_dir / sample_indexes[index]
            sample_path.write_bytes(rotation_path.read_bytes())
        print(f"{index:02d} {content['format']:10s} {content['post_key']}: passed")


if __name__ == "__main__":
    main()
