from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PIL import Image

from backend.story_four import (
    TAROT_START_DATE,
    TAROT_TOPICS,
    TEND,
    build_slot_content,
    render_slot_story,
)
from backend.story_quality import TAROT_DIR, validate_story_asset


def _facts(day: date) -> dict:
    sign = next(iter(TEND))
    return {
        "target_date": day.isoformat(),
        "moon": {"sign": sign, "degree_in_sign": 0.0},
        "moon_phase": {"name": "", "illumination_percent": 0.0},
        "moon_ingress": None,
        "major_aspects": [],
    }


def main() -> None:
    for number in range(22):
        source = TAROT_DIR / f"major-{number:02d}-rws1909-v1.jpeg"
        if not source.is_file() or source.stat().st_size < 100_000:
            raise RuntimeError(f"missing or undersized tarot art: {source}")
        with Image.open(source) as image:
            image.verify()

    output_root = Path("generated") / "tarot-art-preflight"
    for offset in range(len(TAROT_TOPICS)):
        day = TAROT_START_DATE + timedelta(days=offset)
        content = build_slot_content(_facts(day), "evening")
        output = output_root / f"{day.isoformat()}-{content['card_number']:02d}.jpg"
        render_slot_story(content, day, output)
        report = validate_story_asset(output, content, day)
        if not report.get("tarot_card_art", {}).get("detected"):
            raise RuntimeError(f"tarot art check was not recorded: {output}")

    print(f"verified 22 card files and {len(TAROT_TOPICS)} rendered tarot topics")


if __name__ == "__main__":
    main()
