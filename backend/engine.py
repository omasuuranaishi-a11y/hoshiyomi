from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
from typing import Any

try:
    import swisseph as swe
except ImportError:  # Local preview still works before deployment dependencies are installed.
    swe = None

SIGNS = ["牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座", "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"]
PLANETS = ["太陽", "月", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]

HOUSE_DOMAINS = {
    1: "自分らしさ、第一印象、始め方",
    2: "お金、持ち物、安心できる土台",
    3: "会話、学び、近場の移動",
    4: "家、家族、居場所、休息",
    5: "楽しみ、創作、遊び、自己表現",
    6: "体調、習慣、仕事の手順",
    7: "対人関係、約束、相談",
    8: "深い話、共有、お金の受け渡し",
    9: "学び、発信、遠くを見る視点",
    10: "仕事、役割、表に出ること",
    11: "仲間、未来計画、コミュニティ",
    12: "休息、手放し、内側の整理",
}

ASPECTS = {
    "重なって": (0, 8, 5),
    "なじんで": (60, 5, 3),
    "支え合って": (120, 6, 4),
    "見直しを促して": (90, 6, 4),
    "向き合って": (180, 7, 5),
}


@dataclass(frozen=True)
class BodyPosition:
    planet: str
    degree: float
    sign: str
    house: int


def _julian_day(day: date) -> int:
    return day.toordinal() + 1721425


def _seed_from_birth(birth_date: date, birth_time: str | None) -> int:
    minutes = 720
    if birth_time:
        try:
            hour, minute = birth_time.split(":")[:2]
            minutes = int(hour) * 60 + int(minute)
        except ValueError:
            minutes = 720
    return _julian_day(birth_date) * 37 + minutes * 11


def _pseudo_degree(seed: int, index: int, day: date) -> float:
    cycle = (seed * (index + 3) + _julian_day(day) * (index + 17)) % 36000
    return cycle / 100


def _sign_for(degree: float) -> str:
    return SIGNS[int(degree // 30) % 12]


def _house_for(degree: float, seed: int) -> int:
    asc = (seed * 0.37) % 360
    return int(((degree - asc) % 360) // 30) + 1


def _positions(birth_date: date, birth_time: str | None, target_date: date) -> list[BodyPosition]:
    seed = _seed_from_birth(birth_date, birth_time)
    positions = []
    if swe is not None:
        jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        planet_ids = [swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO]
        for index, (planet, planet_id) in enumerate(zip(PLANETS, planet_ids)):
            degree = float(swe.calc_ut(jd, planet_id)[0][0] % 360)
            positions.append(BodyPosition(planet, degree, _sign_for(degree), _house_for(degree, seed + index * 19)))
        return positions

    for index, planet in enumerate(PLANETS):
        degree = _pseudo_degree(seed, index, target_date)
        positions.append(BodyPosition(planet, degree, _sign_for(degree), _house_for(degree, seed + index * 19)))
    return positions


def _angle(a: float, b: float) -> float:
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def _score_pair(a: BodyPosition, b: BodyPosition) -> dict[str, Any] | None:
    actual = _angle(a.degree, b.degree)
    best = None
    for label, (target, orb, weight) in ASPECTS.items():
        distance = abs(actual - target)
        if distance <= orb:
            score = weight + (orb - distance) / orb * 3
            candidate = {
                "planets": [a.planet, b.planet],
                "aspect": label,
                "angle": round(actual, 1),
                "score": round(score, 2),
                "houses": [a.house, b.house],
                "domains": [HOUSE_DOMAINS[a.house], HOUSE_DOMAINS[b.house]],
            }
            if best is None or candidate["score"] > best["score"]:
                best = candidate
    return best


def _fallback_pairs(positions: list[BodyPosition]) -> list[dict[str, Any]]:
    pairs = []
    for left, right, aspect in [(0, 1, "重なって"), (2, 4, "支え合って"), (3, 5, "見直しを促して")]:
        a = positions[left]
        b = positions[right]
        pairs.append({
            "planets": [a.planet, b.planet],
            "aspect": aspect,
            "angle": round(_angle(a.degree, b.degree), 1),
            "score": 3.0,
            "houses": [a.house, b.house],
            "domains": [HOUSE_DOMAINS[a.house], HOUSE_DOMAINS[b.house]],
        })
    return pairs


def calculate_reading(
    birth_date: str,
    birth_time: str | None = None,
    target_date: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    born = datetime.strptime(birth_date, "%Y-%m-%d").date()
    target = datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else date.today()
    positions = _positions(born, birth_time, target)

    pairs = []
    for i, first in enumerate(positions):
        for second in positions[i + 1:]:
            pair = _score_pair(first, second)
            if pair:
                pairs.append(pair)

    pairs = sorted(pairs, key=lambda item: item["score"], reverse=True)[:3]
    if len(pairs) < 3:
        pairs = (pairs + _fallback_pairs(positions))[:3]

    important_planets = []
    for pair in pairs:
        for planet in pair["planets"]:
            if planet not in important_planets:
                important_planets.append(planet)

    return {
        "name": name or "あなた",
        "birth_date": birth_date,
        "birth_time": birth_time or "",
        "target_date": target.isoformat(),
        "positions": [position.__dict__ for position in positions],
        "highlights": pairs,
        "important_planets": important_planets[:4],
        "moon_phase_hint": round((math.sin(_julian_day(target) / 29.53) + 1) * 50),
    }

