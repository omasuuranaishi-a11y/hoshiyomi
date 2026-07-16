from __future__ import annotations

from datetime import date
from typing import Any

from .story_copy import DailyStoryCopy, StorySlide


SIGN_GUIDANCE: dict[str, tuple[str, str, str, str]] = {
    "牡羊座": (
        "小さく始める朝",
        "勢いが出やすいぶん、全部を一度に進めなくても大丈夫。最初の一歩を小さくすると、今日の流れが軽くなります。",
        "10分だけ、気になっていたことを始める",
        "完璧な準備より、いま動かせる小さな一つを選んでみる。始めたあとの景色が、次の答えを見せてくれそうです。",
    ),
    "牡牛座": (
        "心地よさを基準に",
        "急いで答えを出すより、手触りや居心地を確かめたい日。いつものペースを守ることも、立派な前進です。",
        "温かい飲み物を、座ってゆっくり味わう",
        "予定を詰める前に、体と気持ちがほっとする時間を一つ置いてみる。落ち着くほど、本当に必要なことが見えます。",
    ),
    "双子座": (
        "言葉を軽やかに",
        "考えが次々に浮かびやすい日。頭の中だけでまとめようとせず、短い言葉にして外へ出すと整理が進みます。",
        "気になることを三行だけメモに書く",
        "結論を急がず、まず言葉にして眺めてみる。誰かに話す前の小さなメモが、気持ちをほどいてくれそうです。",
    ),
    "蟹座": (
        "安心できる方へ",
        "周りを気づかうほど、自分の本音が後回しになりやすい日。まず自分が安心できる順番を選んで大丈夫です。",
        "自分のための予定を一つ先に入れる",
        "誰かのために動く前に、自分の気持ちにも席を用意してみる。小さな安心が、今日のやさしさを支えてくれます。",
    ),
    "獅子座": (
        "自分らしさを一つ",
        "人の期待に合わせすぎず、自分がうれしいと思える選択を一つ。大げさでなくても、その実感が今日の軸になります。",
        "好きな色や香りを、今日の装いに足す",
        "目立つことより、自分が納得できる選び方を大切にしてみる。小さな『好き』が、今日の表情を明るくします。",
    ),
    "乙女座": (
        "一つずつ整える",
        "気になる点が見つかりやすい日。でも全部を直す必要はありません。暮らしの一か所だけ整えると、心にも余白が戻ります。",
        "目につく場所を一か所だけ片づける",
        "大きく変える前に、手の届く範囲を一つ整えてみる。小さな完了が、次に進む安心をつくってくれます。",
    ),
    "天秤座": (
        "心地よい間を選ぶ",
        "自分と相手、仕事と休息。その間にちょうどよい場所を探したい日です。どちらか一方に決めなくても大丈夫。",
        "返事の前に、ひと呼吸だけ間を置く",
        "すぐに正解を選ばず、双方が少し楽になる形を探してみる。丁寧な間が、やわらかな関係をつくります。",
    ),
    "蠍座": (
        "本音を静かに確認",
        "表面的に済ませたくない気持ちが出やすい日。答えを誰かに見せる前に、自分だけの本音を確かめてみましょう。",
        "誰にも見せない本音を、一行だけ書く",
        "深く考える力を、心配ではなく理解のために使ってみる。言葉になった本音が、次の選択を静かに支えます。",
    ),
    "射手座": (
        "視線を少し遠くへ",
        "目の前の用事だけで一日を埋めず、少し先の楽しみも思い出したい日。小さな好奇心が流れを変えてくれます。",
        "行ってみたい場所を一つ保存する",
        "義務の合間に、これから楽しみなことを一つ置いてみる。先にある光が、今日の足取りを軽くしてくれます。",
    ),
    "山羊座": (
        "続けられる形を選ぶ",
        "頑張ることより、無理なく続く形を考えたい日。今日できる量に整えるほど、結果につながる道が見えてきます。",
        "今日やる量を、いつもの八割に決める",
        "大きな目標を、いま終えられる大きさに分けてみる。確かな一歩が、自分への信頼を少しずつ育てます。",
    ),
    "水瓶座": (
        "いつもと違う角度",
        "決まりきったやり方に、少し窮屈さを感じるかもしれません。小さな工夫を一つ試すと、新しい余白が生まれます。",
        "いつもの順番を一つだけ入れ替える",
        "正しさより、自分に合う方法を試してみる。小さな変更が、思っていた以上に気分を軽くしてくれそうです。",
    ),
    "魚座": (
        "感じる時間を大切に",
        "言葉になる前の気持ちを、急いで片づけなくてよい日。音や香り、景色を使うと、心の輪郭がやさしく戻ります。",
        "好きな音を一曲、何もせずに聴く",
        "考えて解決する前に、感じていることをそのまま受け止めてみる。静かな時間が、次の一歩を教えてくれます。",
    ),
}


ASPECT_GUIDANCE: dict[str, tuple[str, str]] = {
    "コンジャンクション": (
        "重なる力を一つに",
        "二つのテーマが重なりやすい空です。力を分散させず、いま大切な一つへ意識を集めてみましょう。",
    ),
    "オポジション": (
        "両方の気持ちを見る",
        "向かい合う二つのテーマが見えやすい空です。すぐ片方を消さず、どちらの声にも理由があると考えてみて。",
    ),
    "スクエア": (
        "流れを組み替える",
        "少し噛み合わない感じは、やり方を見直す合図かもしれません。無理に押し切らず、順番を一つ変えてみましょう。",
    ),
    "トライン": (
        "得意な流れを使う",
        "自然に進みやすい流れがあります。遠慮して小さくまとめず、いま素直にできることを活かしてみましょう。",
    ),
    "セクスタイル": (
        "小さな機会を拾う",
        "少し手を伸ばすと動きやすい空です。完璧なタイミングを待たず、気になることを一つ試してみましょう。",
    ),
}


PHASE_NOTES: tuple[str, ...] = (
    "今日は、できたことを一つ数えるだけでも十分です。",
    "答えを急がず、今の自分に合う速さを選んでみて。",
    "予定より、心が少し軽くなる方を一つ選びましょう。",
    "小さな違和感は、暮らしを調整するためのヒントです。",
)


def generate_free_story_copy(facts: dict[str, Any]) -> DailyStoryCopy:
    """Build varied Japanese story copy without any network or AI API call."""

    moon = facts["moon"]
    phase = facts["moon_phase"]
    aspects = facts.get("major_aspects") or []
    ingress = facts.get("moon_ingress")
    target = date.fromisoformat(facts["target_date"])
    seed = target.toordinal()

    sign_title, sign_body, sign_action, sign_step_body = SIGN_GUIDANCE.get(
        moon["sign"], SIGN_GUIDANCE["乙女座"]
    )
    main = aspects[0] if aspects else None

    if main:
        first, second = main["planets"]
        aspect_title, aspect_note = ASPECT_GUIDANCE.get(
            main["aspect"], ("今日の流れを読む", "いまの流れを丁寧に確かめたい空です。")
        )
        sky_title = aspect_title
        sky_body = (
            f"月は{moon['sign']}。{first}と{second}の{main['aspect']}が見られます。"
            f"{aspect_note}"
        )
        sky_action = (
            "いま変えられる順番を一つ見つける"
            if main["aspect"] in {"スクエア", "オポジション"}
            else "気になったことを一つ、小さく試してみる"
        )
    else:
        sky_title = sign_title
        sky_body = (
            f"今日は{phase['name']}、月は{moon['sign']}にいます。"
            f"{PHASE_NOTES[seed % len(PHASE_NOTES)]}"
        )
        sky_action = sign_action

    if ingress:
        daily_title = f"{ingress['local_time']}ごろ空気が変わる"
        daily_body = (
            f"月は{ingress['local_time']}ごろ、{ingress['from']}から{ingress['to']}へ。"
            "午前と午後で気分や優先順位が変わっても、自然な流れとして受け止めて大丈夫です。"
        )
    else:
        daily_title = sign_title
        daily_body = sign_body

    step_titles = (
        "今日の一つを決めよう",
        "自分のペースを戻そう",
        "小さな余白をつくろう",
        "暮らしに星を使おう",
    )
    step_title = step_titles[seed % len(step_titles)]

    return DailyStoryCopy(
        theme=f"{moon['sign']}の月と{phase['name']}",
        caption=(
            f"{facts['target_date']}の空を、今日の暮らしに使える言葉へ。"
            "出生図を使わない、みんなのための星よみです。"
        ),
        slides=[
            StorySlide(
                eyebrow="今日の星よみ",
                title=sky_title,
                body=sky_body,
                action=sky_action,
            ),
            StorySlide(
                eyebrow="40代の毎日に",
                title=daily_title,
                body=daily_body,
                action=sign_action,
            ),
            StorySlide(
                eyebrow="今日の小さな一歩",
                title=step_title,
                body=sign_step_body,
                action=sign_action,
            ),
        ],
    )

