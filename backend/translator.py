from __future__ import annotations

from typing import Any

from .keywords import ACTION_BANK, ASPECT_TONES, THEME_WORDS


def _pick(items: tuple[str, ...], index: int) -> str:
    return items[index % len(items)]


def _theme_sentence(highlight: dict[str, Any], index: int) -> str:
    first, second = highlight["planets"]
    first_word = _pick(THEME_WORDS[first], index)
    second_word = _pick(THEME_WORDS[second], index + 1)
    tone = ASPECT_TONES[highlight["aspect"]]
    domain_a, domain_b = highlight["domains"]
    return (
        f"{first}の{first_word}と{second}の{second_word}が{highlight['aspect']}います。"
        f"{tone}。生活の場面では、{domain_a}と、{domain_b}が重なって見えやすいでしょう。"
    )


def _action_sentence(highlight: dict[str, Any], index: int) -> str:
    house = highlight["houses"][index % 2]
    action = _pick(ACTION_BANK[house], index)
    return f"今日の行動は、{action}くらいの小ささがちょうどよさそうです。"


def build_message(reading: dict[str, Any]) -> str:
    highlights = reading["highlights"]
    main, second, third = highlights
    lead = (
        f"{reading['name']}さんの今日の星まわりでは、"
        f"{main['planets'][0]}と{main['planets'][1]}が特に目立っています。"
        "急いで大きく変えるより、今ある流れを丁寧に扱うほど整いやすい日です。"
    )
    parts = [
        lead,
        _theme_sentence(main, 0),
        _theme_sentence(second, 1),
        _theme_sentence(third, 2),
        _action_sentence(main, 0),
        _action_sentence(second, 1),
        "迷ったときは、誰かに説明する前に、自分の中で言葉を整える時間を少し取ってください。今日の星は、派手な追い風というより、足元を確かめるための明かりとして使うと味方になります。",
    ]
    message = "\n\n".join(parts)
    if len(message) < 400:
        message += "\n\nひとつ終えたら、次を考える。その順番を守るだけでも、気持ちの散らばりは自然に落ち着いていきます。"
    if len(message) > 700:
        message = message[:690].rsplit("。", 1)[0] + "。"
    return message


def summarize_theme(reading: dict[str, Any]) -> str:
    highlight = reading["highlights"][0]
    first, second = highlight["planets"]
    return f"いまの星まわりでは、{first}と{second}が{highlight['aspect']}います。"
