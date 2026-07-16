from __future__ import annotations

from datetime import date, timedelta

from backend.story_copy_free import generate_free_story_copy
from backend.story_sky_daily import build_daily_sky


def test_free_copy_uses_real_sky_and_never_needs_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    facts = build_daily_sky(date(2026, 7, 17))

    copy = generate_free_story_copy(facts)

    assert len(copy.slides) == 3
    assert facts["moon"]["sign"] in copy.theme
    assert facts["major_aspects"][0]["aspect"] in copy.slides[0].body
    assert all(20 <= len(slide.body) <= 125 for slide in copy.slides)


def test_free_copy_varies_across_days() -> None:
    start = date(2026, 7, 17)
    titles = set()
    actions = set()

    for offset in range(10):
        copy = generate_free_story_copy(build_daily_sky(start + timedelta(days=offset)))
        titles.add(tuple(slide.title for slide in copy.slides))
        actions.add(copy.slides[2].action)

    assert len(titles) >= 5
    assert len(actions) >= 3

