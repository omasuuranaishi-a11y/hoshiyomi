"""User-approved four-program rollout. Content dates are JST dates."""
from datetime import date
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = date(2026, 9, 7)
VERSION = "2026-09-07-four-programs-v1"
COLUMNS = json.loads((ROOT / "story_columns.json").read_text(encoding="utf-8"))


def build_program_content(facts, slot):
    day = date.fromisoformat(facts["target_date"])
    if day < START:
        return None
    if slot == "night":
        index = (day - START).days % len(COLUMNS)
        post = COLUMNS[index]
        return dict(slot=slot, content_kind="column_20260907",
                    title="暮らしと思考のミニコラム", number=index+1,
                    headline=post["headline"], paragraphs=post["paragraphs"],
                    column="\n\n".join(post["paragraphs"]),
                    scene_key=f"life_column_{index}", copy_version=VERSION,
                    context=f"月は{facts['moon']['sign']}")
    return None
