from __future__ import annotations

from datetime import date
import math
from pathlib import Path
import random
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .story_copy import DailyStoryCopy, StorySlide
from .story_renderer import HEIGHT, WIDTH, _font, _wrap_text, resolve_font_path


WHITE = (255, 252, 244, 255)
GOLD = (235, 196, 112, 255)
GOLD_SOFT = (220, 184, 108, 210)
INK = (42, 33, 29, 255)
PARCHMENT = (239, 218, 174, 244)
BLUE = (71, 132, 226, 220)
RED = (229, 79, 84, 220)

SIGN_SHORT = [
    "牡羊", "牡牛", "双子", "蟹", "獅子", "乙女",
    "天秤", "蠍", "射手", "山羊", "水瓶", "魚",
]
PLANET_SHORT = {
    "太陽": "日", "月": "月", "水星": "水", "金星": "金", "火星": "火",
    "木星": "木", "土星": "土", "天王星": "天", "海王星": "海", "冥王星": "冥",
}
ASPECT_COLORS = {
    "スクエア": RED,
    "オポジション": RED,
    "トライン": BLUE,
    "セクスタイル": BLUE,
    "コンジャンクション": GOLD_SOFT,
}


def _mix(left: tuple[int, int, int], right: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * amount) for a, b in zip(left, right))


def _background(target: date, slide_number: int) -> Image.Image:
    image = Image.new("RGBA", (WIDTH, HEIGHT), (3, 23, 39, 255))
    draw = ImageDraw.Draw(image)
    stops = [
        (0.00, (2, 26, 44)),
        (0.25, (5, 88, 101)),
        (0.39, (244, 158, 80)),
        (0.55, (30, 88, 77)),
        (1.00, (3, 16, 29)),
    ]
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        for index in range(len(stops) - 1):
            start_at, start_color = stops[index]
            end_at, end_color = stops[index + 1]
            if start_at <= ratio <= end_at:
                local = (ratio - start_at) / (end_at - start_at)
                draw.line((0, y, WIDTH, y), fill=(*_mix(start_color, end_color, local), 255))
                break

    seed = int(target.strftime("%Y%m%d")) + slide_number * 1009
    rng = random.Random(seed)
    stars = Image.new("RGBA", image.size, (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(stars)
    for _ in range(86):
        x = rng.randint(26, WIDTH - 26)
        y = rng.randint(22, 560)
        radius = rng.choice([1, 1, 2, 2, 3])
        alpha = rng.randint(90, 225)
        star_draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(244, 246, 224, alpha),
        )
    for _ in range(8):
        x = rng.randint(55, WIDTH - 55)
        y = rng.randint(60, 480)
        star_draw.line((x - 10, y, x + 10, y), fill=(255, 255, 240, 190), width=2)
        star_draw.line((x, y - 10, x, y + 10), fill=(255, 255, 240, 190), width=2)
        star_draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 245, 235))
    image.alpha_composite(stars)

    landscape = Image.new("RGBA", image.size, (0, 0, 0, 0))
    land = ImageDraw.Draw(landscape)
    for base_y, color, amplitude, phase in [
        (730, (24, 91, 83, 230), 36, 9),
        (820, (15, 69, 66, 245), 52, 13),
        (940, (9, 50, 54, 255), 68, 17),
    ]:
        points = []
        for x in range(-40, WIDTH + 81, 40):
            wave = math.sin((x + phase * 17) / 145) * amplitude
            points.append((x, round(base_y + wave + rng.randint(-13, 13))))
        points.extend([(WIDTH + 80, HEIGHT), (-40, HEIGHT)])
        land.polygon(points, fill=color)
    for index in range(12):
        start_x = -180 + index * 130
        land.line((start_x, HEIGHT, 470 + index * 18, 850), fill=(125, 145, 91, 55), width=4)
    for y in range(1020, 1880, 130):
        land.arc((-220, y - 180, WIDTH + 260, y + 130), 188, 352, fill=(184, 148, 76, 45), width=3)
    image.alpha_composite(landscape)

    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shade_draw = ImageDraw.Draw(shade)
    for y in range(760, HEIGHT):
        amount = (y - 760) / (HEIGHT - 760)
        shade_draw.line((0, y, WIDTH, y), fill=(1, 10, 20, round(38 + amount * 155)))
    image.alpha_composite(shade)

    vignette = Image.new("L", image.size, 0)
    ImageDraw.Draw(vignette).ellipse((-190, -140, WIDTH + 190, HEIGHT + 260), fill=205)
    vignette = Image.eval(vignette.filter(ImageFilter.GaussianBlur(95)), lambda value: 255 - value)
    darkness = Image.new("RGBA", image.size, (0, 0, 0, 0))
    darkness.putalpha(vignette.point(lambda value: round(value * 0.55)))
    image.alpha_composite(darkness)
    return image


def _polar(center: tuple[int, int], radius: float, longitude: float) -> tuple[float, float]:
    angle = math.radians(longitude - 90)
    return center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius


def _center_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: float,
    font: ImageFont.FreeTypeFont,
    *,
    fill: tuple[int, int, int, int],
    stroke: int = 0,
) -> float:
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    draw.text(
        ((WIDTH - (box[2] - box[0])) / 2, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=(0, 0, 0, 175),
    )
    return y + box[3] - box[1]


def _fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    *,
    start: int,
    minimum: int,
    max_width: int,
    max_lines: int,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    last_font = _font(font_path, minimum)
    last_lines = _wrap_text(draw, text, last_font, max_width)
    for size in range(start, minimum - 1, -2):
        font = _font(font_path, size)
        lines = _wrap_text(draw, text, font, max_width)
        orphan = len(lines) > 1 and len(lines[-1].strip()) == 1
        if len(lines) <= max_lines and not orphan:
            return font, lines
        last_font, last_lines = font, lines
    return last_font, last_lines[:max_lines]


def _center_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    y: float,
    font: ImageFont.FreeTypeFont,
    *,
    fill: tuple[int, int, int, int],
    gap: int,
    stroke: int = 0,
) -> float:
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font, stroke_width=stroke)
        draw.text(
            ((WIDTH - (box[2] - box[0])) / 2, y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke,
            stroke_fill=(0, 0, 0, 175),
        )
        y += box[3] - box[1] + gap
    return y


def _draw_chart(
    image: Image.Image,
    facts: dict[str, Any],
    center: tuple[int, int],
    radius: int,
    font_path: str,
) -> None:
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        (
            center[0] - radius - 20,
            center[1] - radius + 15,
            center[0] + radius + 20,
            center[1] + radius + 55,
        ),
        fill=(0, 0, 0, 145),
    )
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(25)))

    chart = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(chart)
    draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=PARCHMENT,
        outline=(75, 51, 36, 255),
        width=max(4, radius // 70),
    )
    for ratio, width in ((0.94, 3), (0.76, 3), (0.61, 3), (0.53, 2)):
        ring = radius * ratio
        draw.ellipse(
            (center[0] - ring, center[1] - ring, center[0] + ring, center[1] + ring),
            outline=(105, 73, 48, 215),
            width=width,
        )
    for degree in range(0, 360, 5):
        outer = _polar(center, radius * 0.94, degree)
        inner = _polar(center, radius * (0.90 if degree % 30 else 0.76), degree)
        draw.line((*inner, *outer), fill=(99, 69, 46, 185), width=2 if degree % 30 else 3)

    sign_font = _font(font_path, max(17, radius // 15))
    for index, sign in enumerate(SIGN_SHORT):
        x, y = _polar(center, radius * 0.845, index * 30 + 15)
        box = draw.textbbox((0, 0), sign, font=sign_font)
        draw.text(
            (x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2),
            sign,
            font=sign_font,
            fill=(81, 55, 39, 235),
        )

    positions = {item["planet"]: item for item in facts.get("positions", [])}
    endpoint_radius = radius * 0.50
    for aspect in facts.get("major_aspects", []):
        first_name, second_name = aspect["planets"]
        if first_name not in positions or second_name not in positions:
            continue
        first = _polar(center, endpoint_radius, positions[first_name]["longitude"])
        second = _polar(center, endpoint_radius, positions[second_name]["longitude"])
        draw.line(
            (*first, *second),
            fill=ASPECT_COLORS.get(aspect["aspect"], GOLD_SOFT),
            width=max(2, radius // 125),
        )

    planet_font = _font(font_path, max(24, radius // 10))
    retro_font = _font(font_path, max(13, radius // 23))
    last_longitude: float | None = None
    close_count = 0
    for item in sorted(positions.values(), key=lambda value: value["longitude"]):
        longitude = float(item["longitude"])
        close_count = close_count + 1 if last_longitude is not None and (longitude - last_longitude) % 360 < 10 else 0
        last_longitude = longitude
        marker = _polar(center, radius * 0.53, longitude)
        label = _polar(center, radius * (0.66 - min(close_count, 2) * 0.075), longitude)
        draw.ellipse((marker[0] - 5, marker[1] - 5, marker[0] + 5, marker[1] + 5), fill=(73, 50, 37, 245))
        short = PLANET_SHORT.get(item["planet"], item["planet"][:1])
        box = draw.textbbox((0, 0), short, font=planet_font)
        text_x = label[0] - (box[2] - box[0]) / 2
        text_y = label[1] - (box[3] - box[1]) / 2
        draw.rounded_rectangle(
            (text_x - 7, text_y - 5, text_x + box[2] - box[0] + 7, text_y + box[3] - box[1] + 7),
            radius=9,
            fill=(255, 244, 211, 190),
        )
        draw.text((text_x, text_y), short, font=planet_font, fill=INK)
        if item.get("retrograde"):
            draw.text(
                (text_x + box[2] - box[0] + 4, text_y - 5),
                "R",
                font=retro_font,
                fill=(170, 47, 50, 255),
            )

    center_radius = radius * 0.12
    draw.ellipse(
        (
            center[0] - center_radius,
            center[1] - center_radius,
            center[0] + center_radius,
            center[1] + center_radius,
        ),
        fill=(47, 42, 39, 235),
        outline=(235, 205, 138, 255),
        width=2,
    )
    center_font = _font(font_path, max(14, radius // 20))
    label = "07:00"
    box = draw.textbbox((0, 0), label, font=center_font)
    draw.text(
        (center[0] - (box[2] - box[0]) / 2, center[1] - (box[3] - box[1]) / 2),
        label,
        font=center_font,
        fill=WHITE,
    )
    image.alpha_composite(chart)


def _draw_slide(
    slide: StorySlide,
    facts: dict[str, Any],
    target: date,
    slide_number: int,
    font_path: str,
) -> Image.Image:
    image = _background(target, slide_number)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((12, 12, WIDTH - 13, HEIGHT - 13), outline=(195, 121, 255, 210), width=6)
    draw.rectangle((25, 25, WIDTH - 26, HEIGHT - 26), outline=(255, 255, 255, 120), width=2)

    _center_text(draw, "きょうの星よみ", 56, _font(font_path, 54), fill=WHITE, stroke=2)
    _center_text(
        draw,
        f"{target.year} . {target.month} . {target.day}",
        132,
        _font(font_path, 34),
        fill=(255, 255, 255, 235),
        stroke=2,
    )
    account = "@omasu_horoscope"
    account_font = _font(font_path, 24)
    account_box = draw.textbbox((0, 0), account, font=account_font)
    draw.text(
        (WIDTH - 54 - (account_box[2] - account_box[0]), 42),
        account,
        font=account_font,
        fill=(255, 255, 255, 185),
        stroke_width=1,
        stroke_fill=(0, 0, 0, 130),
    )

    if slide_number == 1:
        chart_center, chart_radius, panel_top = (WIDTH // 2, 650), 350, 1040
    else:
        chart_center, chart_radius, panel_top = (WIDTH // 2, 505), 255, 805
    _draw_chart(image, facts, chart_center, chart_radius, font_path)

    panel_bottom = 1850
    draw.rounded_rectangle(
        (58, panel_top, WIDTH - 58, panel_bottom),
        radius=44,
        fill=(2, 14, 27, 186),
        outline=(255, 255, 255, 72),
        width=2,
    )
    _center_text(draw, slide.eyebrow, panel_top + 44, _font(font_path, 32), fill=GOLD, stroke=1)
    title_font, title_lines = _fit(
        draw,
        slide.title,
        font_path,
        start=68,
        minimum=50,
        max_width=880,
        max_lines=2,
    )
    title_end = _center_lines(
        draw,
        title_lines,
        panel_top + 96,
        title_font,
        fill=WHITE,
        gap=12,
        stroke=2,
    )
    draw.line((250, title_end + 22, WIDTH - 250, title_end + 22), fill=GOLD_SOFT, width=3)

    body_font, body_lines = _fit(
        draw,
        slide.body,
        font_path,
        start=44,
        minimum=34,
        max_width=850,
        max_lines=6,
    )
    _center_lines(
        draw,
        body_lines,
        max(title_end + 78, panel_top + 265),
        body_font,
        fill=(255, 255, 255, 242),
        gap=20,
        stroke=2,
    )

    action_top = panel_bottom - 160
    draw.rounded_rectangle(
        (98, action_top, WIDTH - 98, panel_bottom - 38),
        radius=34,
        fill=(75, 52, 86, 222),
        outline=(238, 203, 125, 220),
        width=3,
    )
    action_font, action_lines = _fit(
        draw,
        slide.action,
        font_path,
        start=38,
        minimum=29,
        max_width=780,
        max_lines=2,
    )
    line_height = draw.textbbox((0, 0), "あ", font=action_font)[3] + 12
    action_y = action_top + ((panel_bottom - 38 - action_top) - len(action_lines) * line_height) / 2
    _center_lines(
        draw,
        action_lines,
        action_y,
        action_font,
        fill=WHITE,
        gap=10,
        stroke=1,
    )

    counter_font = _font(font_path, 25)
    counter = f"{slide_number} / 3"
    box = draw.textbbox((0, 0), counter, font=counter_font)
    draw.text(
        ((WIDTH - (box[2] - box[0])) / 2, 1871),
        counter,
        font=counter_font,
        fill=(255, 255, 255, 180),
    )
    return image.convert("RGB")


def render_story_images(
    copy: DailyStoryCopy,
    target_date: str | date,
    *,
    facts: dict[str, Any] | None = None,
    output_root: str | Path | None = None,
) -> list[Path]:
    target = date.fromisoformat(target_date) if isinstance(target_date, str) else target_date
    if facts is None:
        from .story_sky_daily import build_daily_sky
        facts = build_daily_sky(target)

    root = Path(
        output_root
        or Path(__file__).resolve().parents[1] / "generated" / "story_assets"
    )
    output_dir = root / target.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    font_path = resolve_font_path()

    paths = []
    for index, slide in enumerate(copy.slides, start=1):
        image = _draw_slide(slide, facts, target, index, font_path)
        path = output_dir / f"slide-{index}.jpg"
        image.save(path, format="JPEG", quality=95, optimize=True, subsampling=0)
        paths.append(path)
    return paths
