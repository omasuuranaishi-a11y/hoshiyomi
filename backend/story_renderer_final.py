from __future__ import annotations

from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .story_copy import DailyStoryCopy, StorySlide
from .story_renderer import (
    GOLD,
    HEIGHT,
    INK,
    MUTED,
    PAPER,
    PURPLE,
    PURPLE_LIGHT,
    WHITE,
    WIDTH,
    _draw_centered_lines,
    _draw_constellation,
    _font,
    _wrap_text,
    resolve_font_path,
)


def _fit_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    *,
    start_size: int,
    minimum_size: int,
    max_width: int,
    max_lines: int,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    last_font = _font(font_path, minimum_size)
    last_lines = _wrap_text(draw, text, last_font, max_width)
    for size in range(start_size, minimum_size - 1, -2):
        font = _font(font_path, size)
        lines = _wrap_text(draw, text, font, max_width)
        orphan = len(lines) > 1 and len(lines[-1].strip()) == 1
        if len(lines) <= max_lines and not orphan:
            return font, lines
        last_font, last_lines = font, lines
    if len(last_lines) > 1 and len(last_lines[-1]) == 1 and len(last_lines[-2]) > 2:
        last_lines[-1] = last_lines[-2][-1] + last_lines[-1]
        last_lines[-2] = last_lines[-2][:-1]
    return last_font, last_lines


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
    eyebrow_font = _font(font_path, 42)
    body_font = _font(font_path, 45)
    title_font, title_lines = _fit_lines(
        draw,
        slide.title,
        font_path,
        start_size=76,
        minimum_size=54,
        max_width=820,
        max_lines=2,
    )
    action_font, action_lines = _fit_lines(
        draw,
        slide.action,
        font_path,
        start_size=40,
        minimum_size=30,
        max_width=720,
        max_lines=2,
    )

    draw.text((80, 112), target.strftime("%Y.%m.%d"), font=small, fill=MUTED)
    account = "@omasu_horoscope"
    account_width = draw.textlength(account, font=small)
    draw.text((WIDTH - 80 - account_width, 112), account, font=small, fill=MUTED)

    eyebrow_width = draw.textlength(slide.eyebrow, font=eyebrow_font)
    draw.text(
        ((WIDTH - eyebrow_width) / 2, 580),
        slide.eyebrow,
        font=eyebrow_font,
        fill=PURPLE,
    )

    title_y = _draw_centered_lines(
        draw,
        title_lines,
        title_font,
        675,
        fill=INK,
        line_gap=18,
    )
    draw.line((320, title_y + 24, 760, title_y + 24), fill=GOLD, width=3)

    body_lines = _wrap_text(draw, slide.body, body_font, 780)
    body_y = max(title_y + 92, 930)
    _draw_centered_lines(draw, body_lines, body_font, body_y, fill=INK, line_gap=25)

    draw.rounded_rectangle((130, 1588, 950, 1750), radius=36, fill=PURPLE)
    action_line_height = max(
        52,
        draw.textbbox((0, 0), "あ", font=action_font)[3]
        - draw.textbbox((0, 0), "あ", font=action_font)[1]
        + 14,
    )
    action_y = 1669 - (len(action_lines) * action_line_height) // 2
    _draw_centered_lines(
        draw,
        action_lines,
        action_font,
        action_y,
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
    root = Path(
        output_root
        or Path(__file__).resolve().parents[1] / "generated" / "story_assets"
    )
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
