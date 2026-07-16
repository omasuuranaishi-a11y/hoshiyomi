from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field, field_validator


class StorySlide(BaseModel):
    eyebrow: str = Field(min_length=2, max_length=18)
    title: str = Field(min_length=4, max_length=24)
    body: str = Field(min_length=20, max_length=125)
    action: str = Field(min_length=8, max_length=48)

    @field_validator("eyebrow", "title", "body", "action")
    @classmethod
    def normalize_spacing(cls, value: str) -> str:
        return " ".join(value.replace("\n", " ").split())


class DailyStoryCopy(BaseModel):
    theme: str = Field(min_length=6, max_length=40)
    caption: str = Field(min_length=15, max_length=180)
    slides: list[StorySlide] = Field(min_length=3, max_length=3)


SYSTEM_PROMPT = """あなたは「星よみ専門家 おます」の編集アシスタントです。
40代女性が朝に読み、少し気持ちが軽くなって現実の行動へ移せるInstagramストーリーを作ります。

絶対条件:
- 占星術上の事実は、ユーザーが渡すJSONだけを根拠にする。星座、天体、アスペクト、日時を補完・推測しない。
- 出生図、ハウス、個人鑑定のような言い方をしない。
- 「必ず起きる」「運命」「危険」などの断定や恐怖訴求をしない。
- 医療、法律、金融の助言をしない。
- 専門用語を並べず、必要な用語は日常の言葉に言い換える。
- おますさんらしく、やわらかい話し言葉にする。「〜なんですよね」「〜かもしれません」を自然に混ぜる。
- 「整える」「見直す」「言葉を選ぶ」だけを毎回の結論にしない。渡された直近タイトルとの重複を避ける。
- 絵文字は全体で0〜2個。ハッシュタグは書かない。

3枚の役割:
1枚目: 今日の空で最も大事な事実と、短いテーマ。
2枚目: 家事・子育て・仕事を抱える40代女性の日常へ翻訳する。
3枚目: 今日すぐできる小さな行動で締める。

画像に収まる短さを守り、同じ説明を繰り返さないでください。"""


def _fallback_copy(facts: dict[str, Any]) -> DailyStoryCopy:
    moon = facts["moon"]
    phase = facts["moon_phase"]
    aspects = facts.get("major_aspects") or []
    ingress = facts.get("moon_ingress")
    main = aspects[0] if aspects else None

    if main:
        first, second = main["planets"]
        sky_title = f"{first}と{second}が響く日"
        sky_body = (
            f"月は{moon['sign']}。{first}と{second}の{main['aspect']}が、"
            "いつもの流れに少し違う角度をくれそうです。"
        )
    else:
        sky_title = f"月は{moon['sign']}へ"
        sky_body = (
            f"今日は{phase['name']}、月は{moon['sign']}にいます。"
            "気持ちの動きを急いで答えにせず、まず眺めてみたい朝です。"
        )

    if ingress:
        daily_body = (
            f"月は{ingress['local_time']}ごろ、{ingress['from']}から"
            f"{ingress['to']}へ。午前と午後で気分が変わっても、"
            "どちらも今日の自分です。"
        )
    else:
        daily_body = (
            "家のことも仕事も全部いっぺんに片づけようとしなくて大丈夫。"
            "いま気になっているものを、一つだけ先に扱ってみてください。"
        )

    return DailyStoryCopy(
        theme=f"{moon['sign']}の月と{phase['name']}",
        caption=f"{facts['target_date']}の空を、今日の暮らしに使える言葉へ翻訳しました。",
        slides=[
            StorySlide(
                eyebrow="今日の星よみ",
                title=sky_title,
                body=sky_body,
                action="まずは、いまの気分に名前をつけてみる",
            ),
            StorySlide(
                eyebrow="40代の毎日に",
                title="全部を急がなくていい",
                body=daily_body,
                action="今日いちばん大事な一つを決める",
            ),
            StorySlide(
                eyebrow="今日の小さな一歩",
                title="先に余白をつくろう",
                body=(
                    "予定を増やす前に、やらなくても困らないことを一つ減らしてみる。"
                    "その余白が、次の動きを見つけやすくしてくれます。"
                ),
                action="5分だけ、何もしない時間を予約する",
            ),
        ],
    )


def generate_story_copy(
    facts: dict[str, Any],
    *,
    recent_titles: list[str] | None = None,
    offline: bool = False,
) -> DailyStoryCopy:
    if offline:
        return _fallback_copy(facts)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        if os.getenv("ALLOW_FALLBACK_COPY", "false").lower() == "true":
            return _fallback_copy(facts)
        raise RuntimeError("OPENAI_API_KEY が設定されていません。")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.parse(
            model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "sky_facts": facts,
                            "recent_titles_to_avoid": (recent_titles or [])[-14:],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            text_format=DailyStoryCopy,
        )
        if response.output_parsed is None:
            raise RuntimeError("AIから構造化された文章を受け取れませんでした。")
        return response.output_parsed
    except Exception:
        if os.getenv("ALLOW_FALLBACK_COPY", "false").lower() == "true":
            return _fallback_copy(facts)
        raise
