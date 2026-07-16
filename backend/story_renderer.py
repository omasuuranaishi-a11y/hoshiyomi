from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import random
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from .story_copy import DailyStoryCopy, StorySlide


WIDTH = 1080
HEIGHT = 1920
PAPER = "#F5F0E8"
INK = "#342F2B"
MUTED = "#756D67"
PURPLE = "#88779C"
PURPLE_LIGHT = "#E6DDEA"
GOLD = "#C4A25A"
WHITE = "#FFFCF7"

DEFAULT_FONT_URL = (
    "https://raw.githubusercontent.com/google/fonts/main/"
    "ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf"
)


def _font_candidates() -> Iterable[str]:
    configured = os.getenv("STORY_FONT_PATH", "").strip()
    if configured:
        yield configured
    yield str(Path(__file__).resolve().parents[1] / "assets" / "NotoSansJP-VF.ttf")
    yield "C:/Windows/Fonts/NotoSansJP-VF.ttf"
    yield "C:/Windows/Fonts/YuGothM.ttc"
    yield "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    yield "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf"


def _download_font() -> str | None:
    if os.getenv("STORY_FONT_DOWNLOAD", "true").lower() != "true":
        return None
    cache_dir = Path(os.getenv("STORY_FONT_CACHE_DIR", "/tmp/omasu-story-fonts"))
    cache_path = cache_dir / "NotoSansJP-VF.ttf"
    if cache_path.exists() and cache_path.stat().st_size > 1_000_000:
        return str(cache_path)

    try:
        import httpx

        cache_dir.mkdir(parents=True, exist_ok=True)
        font_url = os.getenv("STORY_FONT_URL", DEFAULT_FONT_URL)
        with httpx.stream("GET", font_url, follow_redirects=True, timeout=90) as response:
            response.raise_for_status()
            with cache_path.open("wb") as output:
                for chunk in response.iter_bytes():
                    output.write(chunk)
        if cache_path.stat().st_size <= 1_000_000:
            cache_path.unlink(missing_ok=True)
            return None
        return str(cache_path)
    except Exception:
        return None


def resolve_font_path() -> str:
    for candidate in _font_candidates():
        if Path(candidate).exists():
            return candidate
    downloaded = _download_font()
    if downloaded:
        return downloaded
    return "DejaVuSans.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for character in text:
        if character == "\n":
            if current:
                lines.append(current)
                current = ""
            continue
        candidate = current + character
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = character
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    y: int,
    *,
    fill: str,
    line_gap: int,
) -> int:
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        draw.text(((WIDTH - width) / 2, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def _draw_constellation(draw: ImageDraw.ImageDraw, seed: int, top: int) -> None:
    rng = random.Random(seed)
    points = []
    for index in range(8):
        x = 110 + index * 122 + rng.randint(-26, 26)
        y = top + rng.randint(-42, 42)
        points.append((x, y))
    for left, right in zip(points, points[1:]):
        draw.line((left, right), fill=GOLD, width=2)
    for x, y in points:
        radius = rng.choice([3, 4, 6])
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=GOLD)


def _draw_slide(
    slide: StorySlide,
    target: date,
    slide_number: int,
    font_path: str,
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)

    _draw_constellation(draw, int(target.strftime("%Y%m%d")) + slide_number, 235)
    draw.ellipse((760, 110, 1030, 380), fill=PURPLE_LIGHT)
    draw.ellipse((812, 92, 1082, 362), fill=PAPER)
    draw.rounded_rectangle((74, 510, 1006, 1535), radius=48, fill=WHITE)

    small = _font(font_path, 34)
    eyebrow = _font(font_path, 42)
    title = _font(font_path, 76)
    body = _font(font_path, 45)
    action_font = _font(font_path, 40)

    draw.text((80, 112), target.strftime("%Y.%m.%d"), font=small, fill=MUTED)
    account = "@omasu_horoscope"
    account_width = draw.textlength(account, font=small)
    draw.text((WIDTH - 80 - account_width, 112), account, font=small, fill=MUTED)

    eyebrow_width = draw.textlength(slide.eyebrow, font=eyebrow)
    draw.text(((WIDTH - eyebrow_width) / 2, 580), slide.eyebrow, font=eyebrow, fill=PURPLE)

    title_lines = _wrap_text(draw, slide.title, title, 790)
    title_y = _draw_centered_lines(
        draw,
        title_lines,
        title,
        675,
        fill=INK,
        line_gap=20,
    )
    draw.line((320, title_y + 24, 760, title_y + 24), fill=GOLD, width=3)

    body_lines = _wrap_text(draw, slide.body, body, 780)
    body_y = max(title_y + 92, 930)
    _draw_centered_lines(draw, body_lines, body, body_y, fill=INK, line_gap=25)

    draw.rounded_rectangle((130, 1588, 950, 1750), radius=36, fill=PURPLE)
    action_lines = _wrap_text(draw, slide.action, action_font, 690)
    action_total_height = len(action_lines) * 58
    _draw_centered_lines(
        draw,
        action_lines,
        action_font,
        1668 - action_total_height // 2,
        fill=WHITE,
        line_gap=12,
    )

    counter = f"{slide_number} / 3"
    counter_width = draw.textlength(counter, font=small)
    draw.text(((WIDTH - counter_width) / 2, 1810), counter, font=small, fill=MUTED)
    return image


def render_story_images(
    copy: DailyStoryCopy,
    target_date: str | date,
    *,
    output_root: str | Path | None = None,
) -> list[Path]:
    target = date.fromisoformat(target_date) if isinstance(target_date, str) else target_date
    root = Path(output_root or Path(__file__).resolve().parents[1] / "generated" / "story_assets")
    output_dir = root / target.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    font_path = resolve_font_path()

    paths: list[Path] = []
    for index, slide in enumerate(copy.slides, start=1):
        image = _draw_slide(slide, target, index, font_path)
        path = output_dir / f"slide-{index}.jpg"
        image.save(path, format="JPEG", quality=94, optimize=True, subsampling=0)
        paths.append(path)
    return paths
