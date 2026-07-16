from __future__ import annotations

from datetime import date
from typing import Any

from .story_sky import ASPECTS, build_daily_sky as build_raw_daily_sky


DAILY_PLANET_WEIGHT = {
    "月": 12,
    "太陽": 8,
    "水星": 6,
    "金星": 6,
    "火星": 6,
    "木星": 2,
    "土星": 2,
    "天王星": 1,
    "海王星": 1,
    "冥王星": 1,
}
PERSONAL_PLANETS = {"月", "太陽", "水星", "金星", "火星"}


def _smallest_angle(left: float, right: float) -> float:
    distance = abs(left - right) % 360
    return min(distance, 360 - distance)


def _daily_aspects(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for index, first in enumerate(positions):
        for second in positions[index + 1 :]:
            planets = {first["planet"], second["planet"]}
            if not planets.intersection(PERSONAL_PLANETS):
                continue
            actual = _smallest_angle(first["longitude"], second["longitude"])
            allowed_orb = 6.0 if planets.intersection({"月", "太陽"}) else 4.0
            for aspect_name, target in ASPECTS:
                delta = abs(actual - target)
                if delta > allowed_orb:
                    continue
                priority = max(DAILY_PLANET_WEIGHT[planet] for planet in planets)
                exactness = (allowed_orb - delta) / allowed_orb
                candidates.append(
                    {
                        "planets": [first["planet"], second["planet"]],
                        "aspect": aspect_name,
                        "angle": round(actual, 2),
                        "orb": round(delta, 2),
                        "score": round(priority + exactness, 3),
                    }
                )
                break
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:6]


def build_daily_sky(
    target_date: str | date | None = None,
    timezone_name: str | None = None,
    reading_hour: int = 7,
) -> dict[str, Any]:
    facts = build_raw_daily_sky(target_date, timezone_name, reading_hour)
    daily_aspects = _daily_aspects(facts["positions"])
    if daily_aspects:
        facts["major_aspects"] = daily_aspects
    facts["aspect_selection"] = "月・太陽・水星・金星・火星を日運向けに優先"
    return facts
