from datetime import date, timedelta
import json
from pathlib import Path

import pytest
from backend.story_program import (
    HOROSCOPE_COPY_VERSION, HOROSCOPE_CLEAR_START, HOROSCOPE_CLEAR_VERSION,
    CLEAR_HOUSE_ACTIONS, build_program_content,
)
from backend.story_program_render import render_program, validate_program_asset

APPROVED = json.loads((Path(__file__).parent / "fixtures/horoscope-2026-10-21-approved.json").read_text(encoding="utf-8"))


def facts(day):
    return {"target_date": str(day), "moon": {"sign": APPROVED["moon_sign"]},
            "positions": [], "major_aspects": []}


def test_effective_date_keeps_previous_day_on_approved_v3():
    before = build_program_content(facts(HOROSCOPE_CLEAR_START - timedelta(days=1)), "noon")
    after = build_program_content(facts(HOROSCOPE_CLEAR_START), "noon")
    assert before["copy_version"] == HOROSCOPE_COPY_VERSION
    assert after["copy_version"] == HOROSCOPE_CLEAR_VERSION
    assert before["reading_hour_jst"] == after["reading_hour_jst"] == 5


def test_first_day_matches_all_twelve_approved_sample_texts():
    day = date.fromisoformat(APPROVED["target_date"])
    content = build_program_content(facts(day), "noon")
    assert [{"sign": i["sign"], "text": i["text"]} for i in content["items"]] == APPROVED["items"]


def test_five_distinct_actions_rotate_in_order_and_repeat_after_five_days():
    sheets = [build_program_content(facts(HOROSCOPE_CLEAR_START + timedelta(days=i)), "noon") for i in range(6)]
    for item in range(12):
        values = [sheet["items"][item]["text"] for sheet in sheets]
        assert len(set(values[:5])) == 5
        assert values[0] == values[5]
        house = sheets[0]["items"][item]["house"]
        assert all(values[i].endswith(CLEAR_HOUSE_ACTIONS[house - 1][i]) for i in range(5))


@pytest.mark.parametrize("offset", range(5))
def test_new_copy_fits_every_daily_palette_at_approved_size(tmp_path, offset):
    day = HOROSCOPE_CLEAR_START + timedelta(days=offset)
    content = build_program_content(facts(day), "noon")
    original = [item["text"] for item in content["items"]]
    path = render_program(content, day, tmp_path / f"{day}.jpg")
    assert validate_program_asset(path, content, day)["passed"]
    check = content["render_check"]
    assert check["body_px"] == 40 and check["body_alignment"] == "center"
    assert check["sign_names_centered"] and check["decoration_overlap_free"]
    assert all(len(i["rendered_lines"]) == 2 for i in content["items"])
    assert ["".join(i["rendered_lines"]) for i in content["items"]] == original
