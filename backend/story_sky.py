from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
import math
import os
from typing import Any
from zoneinfo import ZoneInfo

try:
    import swisseph as swe
except ImportError:  # pragma: no cover - deployment installs pyswisseph.
    swe = None


SIGNS = [
    "牡羊座",
    "牡牛座",
    "双子座",
    "蟹座",
    "獅子座",
    "乙女座",
    "天秤座",
    "蠍座",
    "射手座",
    "山羊座",
    "水瓶座",
    "魚座",
]

PLANETS = [
    ("太陽", "SUN"),
    ("月", "MOON"),
    ("水星", "MERCURY"),
    ("金星", "VENUS"),
    ("火星", "MARS"),
    ("木星", "JUPITER"),
    ("土星", "SATURN"),
    ("天王星", "URANUS"),
    ("海王星", "NEPTUNE"),
    ("冥王星", "PLUTO"),
]

ASPECTS = [
    ("コンジャンクション", 0.0),
    ("セクスタイル", 60.0),
    ("スクエア", 90.0),
    ("トライン", 120.0),
    ("オポジション", 180.0),
]


@dataclass(frozen=True)
class TransitPosition:
    planet: str
    longitude: float
    sign: str
    degree_in_sign: float
    retrograde: bool


def _require_swiss_ephemeris() -> None:
    if swe is None:
        raise RuntimeError(
            "pyswisseph が必要です。requirements.txt をインストールしてください。"
        )


def _planet_id(name: str) -> int:
    _require_swiss_ephemeris()
    return int(getattr(swe, name))


def _to_julian_day(moment: datetime) -> float:
    utc = moment.astimezone(timezone.utc)
    decimal_hour = utc.hour + utc.minute / 60 + utc.second / 3600
    return float(swe.julday(utc.year, utc.month, utc.day, decimal_hour, swe.GREG_CAL))


def _position(planet: str, swe_name: str, moment: datetime) -> TransitPosition:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    values = swe.calc_ut(_to_julian_day(moment), _planet_id(swe_name), flags)[0]
    longitude = float(values[0] % 360)
    sign_index = int(longitude // 30) % 12
    return TransitPosition(
        planet=planet,
        longitude=round(longitude, 4),
        sign=SIGNS[sign_index],
        degree_in_sign=round(longitude % 30, 2),
        retrograde=bool(values[3] < 0),
    )


def _all_positions(moment: datetime) -> list[TransitPosition]:
    return [_position(label, swe_name, moment) for label, swe_name in PLANETS]


def _smallest_angle(left: float, right: float) -> float:
    distance = abs(left - right) % 360
    return min(distance, 360 - distance)


def _aspect_orb(first: str, second: str) -> float:
    if "月" in (first, second) or "太陽" in (first, second):
        return 6.0
    return 4.0


def _major_aspects(positions: list[TransitPosition]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for index, first in enumerate(positions):
        for second in positions[index + 1 :]:
            actual = _smallest_angle(first.longitude, second.longitude)
            allowed_orb = _aspect_orb(first.planet, second.planet)
            for aspect_name, target in ASPECTS:
                delta = abs(actual - target)
                if delta > allowed_orb:
                    continue
                daily_weight = 3 if "月" in (first.planet, second.planet) else 0
                luminary_weight = 1 if "太陽" in (first.planet, second.planet) else 0
                exactness = allowed_orb - delta
                found.append(
                    {
                        "planets": [first.planet, second.planet],
                        "aspect": aspect_name,
                        "angle": round(actual, 2),
                        "orb": round(delta, 2),
                        "score": round(exactness + daily_weight + luminary_weight, 3),
                    }
                )
                break
    return sorted(found, key=lambda item: item["score"], reverse=True)[:6]


def _phase_details(sun_longitude: float, moon_longitude: float) -> dict[str, Any]:
    angle = (moon_longitude - sun_longitude) % 360
    phase_names = [
        "新月期",
        "満ちていく三日月期",
        "上弦期",
        "満ちていく凸月期",
        "満月期",
        "欠けていく凸月期",
        "下弦期",
        "欠けていく三日月期",
    ]
    phase_index = int(((angle + 22.5) % 360) // 45)
    illumination = (1 - math.cos(math.radians(angle))) / 2
    return {
        "name": phase_names[phase_index],
        "elongation": round(angle, 2),
        "illumination_percent": round(illumination * 100, 1),
    }


def _moon_sign(moment: datetime) -> str:
    return _position("月", "MOON", moment).sign


def _find_moon_ingress(target: date, tz: ZoneInfo) -> dict[str, str] | None:
    start = datetime.combine(target, time.min, tzinfo=tz)
    end = datetime.combine(target, time.max, tzinfo=tz)
    start_sign = _moon_sign(start)
    previous_moment = start
    previous_sign = start_sign

    probe = start + timedelta(hours=1)
    while probe <= end:
        current_sign = _moon_sign(probe)
        if current_sign != previous_sign:
            low = previous_moment
            high = probe
            while high - low > timedelta(minutes=1):
                midpoint = low + (high - low) / 2
                if _moon_sign(midpoint) == previous_sign:
                    low = midpoint
                else:
                    high = midpoint
            return {
                "from": previous_sign,
                "to": current_sign,
                "local_time": high.strftime("%H:%M"),
            }
        previous_moment = probe
        previous_sign = current_sign
        probe += timedelta(hours=1)
    return None


def build_daily_sky(
    target_date: str | date | None = None,
    timezone_name: str | None = None,
    reading_hour: int = 7,
) -> dict[str, Any]:
    """Return deterministic transit facts for a general-audience daily reading.

    Houses and a natal chart are intentionally excluded. An Instagram-wide reading has
    no single birth time or location, so inventing houses would make the copy look more
    precise than the source data supports.
    """

    _require_swiss_ephemeris()
    timezone_name = timezone_name or os.getenv("STORY_TIMEZONE", "Asia/Tokyo")
    tz = ZoneInfo(timezone_name)
    if target_date is None:
        target = datetime.now(tz).date()
    elif isinstance(target_date, date):
        target = target_date
    else:
        target = date.fromisoformat(target_date)

    reading_moment = datetime.combine(target, time(reading_hour, 0), tzinfo=tz)
    positions = _all_positions(reading_moment)
    position_map = {item.planet: item for item in positions}
    phase = _phase_details(
        position_map["太陽"].longitude,
        position_map["月"].longitude,
    )

    return {
        "target_date": target.isoformat(),
        "timezone": timezone_name,
        "calculated_for": reading_moment.isoformat(),
        "positions": [asdict(item) for item in positions],
        "moon": asdict(position_map["月"]),
        "moon_phase": phase,
        "moon_ingress": _find_moon_ingress(target, tz),
        "major_aspects": _major_aspects(positions),
        "source": "Swiss Ephemeris / tropical zodiac / geocentric positions",
        "editorial_limits": [
            "一般向けのため出生図・ハウスは使用していない",
            "文章では提示された天体位置以外を推測しない",
            "断定・恐怖訴求・医療や金融の助言をしない",
        ],
    }
