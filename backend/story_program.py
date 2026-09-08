"""User-approved four-program rollout. Content dates are JST dates."""
from datetime import date,timedelta
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = date(2026, 9, 7)
VERSION = "2026-09-08-four-programs-v4-celestial"
COLUMNS = json.loads((ROOT / "story_columns.json").read_text(encoding="utf-8"))
DICTIONARY = json.loads((ROOT / "story_dictionary.json").read_text(encoding="utf-8"))
SIGN_NAMES = ("牡羊座","牡牛座","双子座","蟹座","獅子座","乙女座","天秤座","蠍座","射手座","山羊座","水瓶座","魚座")
HOUSE_OPENINGS = ("自分らしさが主役。","手持ちの良さを発見。","会話に新しいヒント。","居場所に心を向けて。","好きなことが入口。","いつもの流れに工夫。","対話で視点が広がる。","信頼を育てる時間。","好奇心が次の扉に。","積み重ねが形になる。","仲間との話に可能性。","静かな時間が充電に。")
HOUSE_ACTIONS = (
 ("今の好みを装いに。","希望を一つ言葉に。","自分のペースで一歩。"),
 ("得意を役立てて。","心地よい物を選ぼう。","手元の道具を活用。"),
 ("気になることを聞く。","発見をメモに残そう。","短い便りを送ろう。"),
 ("好きな花を飾ろう。","くつろぐ場所を作る。","家族と希望を共有。"),
 ("ひらめきを形に。","趣味を少し試そう。","楽しみを誰かに話す。"),
 ("道具を使いやすく。","手順を一つ整える。","体を休める時間も。"),
 ("互いの希望を話そう。","相手の続きを聞こう。","相談の材料を一つ。"),
 ("身近な相手に相談。","大切な話をゆっくり。","協力できる点を探す。"),
 ("未知の分野の本へ。","次の旅を思い描く。","学びを一つ試そう。"),
 ("できたことを共有。","成果を具体的に話す。","次の目標を一つ。"),
 ("やりたいことを話す。","共通の楽しみを探す。","仲間の案を聞こう。"),
 ("浮かぶ考えをメモに。","一人の時間を味わう。","好きな音でひと息。")
)


def editorial_stock():
    """End of distinct dated stock; monitoring replenishes before wraparound."""
    column_days=len(COLUMNS)
    dictionary_days=len(DICTIONARY["cycle"])*len(DICTIONARY["rounds"])
    return {"column_through":str(START+timedelta(days=column_days-1)),
            "dictionary_through":str(START+timedelta(days=dictionary_days-1)),
            "column_days":column_days,"dictionary_days":dictionary_days}


def _horoscope(facts, day):
    moon_index=SIGN_NAMES.index(facts["moon"]["sign"])
    aspects=facts.get("major_aspects",[])
    primary=aspects[0] if aspects else None
    mode=0 if primary and primary["aspect"] in {"トライン","セクスタイル"} else 1 if primary and primary["aspect"]=="コンジャンクション" else 2
    items=[]
    for index,sign in enumerate(SIGN_NAMES):
        house=(moon_index-index)%12+1
        action=HOUSE_ACTIONS[house-1][mode]
        items.append({"sign":sign,"house":house,"text":HOUSE_OPENINGS[house-1]+action,"element":index%4})
    return dict(slot="noon",content_kind="horoscope_20260907",title="12星座 きょうの運勢",items=items,
                moon_sign=facts["moon"]["sign"],scene_key="daily_twelve_signs",copy_version=VERSION,
                method="太陽星座を第1の領域とするサイン単位の一般向け解釈。出生時刻による個人ハウスではない。",
                source_positions=facts["positions"],source_aspects=aspects,reading_hour_jst=8)


def build_program_content(facts, slot):
    day = date.fromisoformat(facts["target_date"])
    if day < START:
        return None
    if slot == "morning" and day > START:
        from .story_four import solar_term,SEASON_NOTES
        term=solar_term(facts);moon=facts['moon'];ing=facts.get('moon_ingress');phase=facts['moon_phase']
        aspect=next(iter(facts.get('major_aspects',[])),None)
        if aspect:
            sky='と'.join(aspect['planets'])+'の'+aspect['aspect']+'。'
            relation={"コンジャンクション":"思いと行動を同じ方向へ向けることが、今日の入口です。","セクスタイル":"会話や小さな試みから、可能性を広げていく読み方ができます。","トライン":"自然にできることや、これまでの経験を活かす読み方ができます。","スクエア":"二つの希望を並べ、今の優先順位を決めることが手がかりになります。","オポジション":"違う立場を並べて見ると、互いの大切にしたい点を見つけやすくなります。"}[aspect['aspect']]
        else:sky=f"月は{moon['sign']}。";relation="今の関心と暮らしの場面を重ねて、今日の取り組み方を考えます。"
        sign_lens=("まず小さく始める","心地よい感覚を確かめる","知りたいことを言葉にする","親しい人や居場所を大切にする","好きなことを表現する","使いやすさを工夫する","相手と希望をすり合わせる","一つのことを深く味わう","新しい見方に触れる","続けられる形を考える","違う方法を試す","心に浮かんだものを受けとめる")[SIGN_NAMES.index(moon['sign'])]
        actions=("食事の相談なら、自分が食べたいものを一つ伝えてから、相手の希望を聞く。最初の材料があると、二人で考えやすくなります。","外出するなら、楽しみたいことと帰る時刻を先に決める。その間に余白を残すと、途中の発見も選べます。","道具を選ぶなら、使う場面を一つ思い浮かべる。誰が、どこで使うかが具体的になるほど、選ぶ条件が見えてきます。","気になる話を聞いたら、知っていることと確かめたいことを分けてメモする。次に調べる場所が一つ見つかります。","何かを頼むなら、してほしいことと希望の時刻を一緒に伝える。相手が返事を考えやすい形に整えてみます。","好きだった場所を思い出し、何が心地よかったかを一つ言葉にする。その条件が、次の楽しみを選ぶ手がかりになります。","新しいことを試すなら、最初は道具や時間を一つ決める。実際にやってみた感触から、次の工夫を考えます。")
        return dict(slot=slot,content_kind="calendar_20260907",title="きょうの暦と月",term=term,season_note=SEASON_NOTES[term],phase=phase['name'],illumination=phase['illumination_percent'],moon_line=f"月は{ing['from']}から、{ing['local_time']}ごろ{ing['to']}へ。" if ing else f"月は一日を通して{moon['sign']}にいます。",hint=sky+relation+f"月が{moon['sign']}の今日は、{sign_lens}ことにも目を向けて。",thinking=actions[(day-START).days%len(actions)],scene_key=f"calendar_{(day-START).days%len(actions)}",copy_version=VERSION)
    if slot == "noon" and day > START:
        return _horoscope(facts, day)
    if slot == "evening":
        offset=(day-START).days
        cycle_index=offset%len(DICTIONARY["cycle"])
        round_index=(offset//len(DICTIONARY["cycle"]))%len(DICTIONARY["rounds"])
        post=DICTIONARY["rounds"][round_index][cycle_index]
        return dict(post,slot=slot,content_kind="dictionary_20260907",title="おますの占い大辞典",
                    scene_key=f"dictionary_{post['id']}_{round_index}",copy_version=VERSION,
                    cycle_index=cycle_index,round_index=round_index,
                    editorial_stock_days=len(DICTIONARY["rounds"])*len(DICTIONARY["cycle"]),
                    sample=False)
    if slot == "night":
        index = (day - START).days % len(COLUMNS)
        post = COLUMNS[index]
        return dict(slot=slot, content_kind="column_20260907",
                    title="暮らしと思考のミニコラム", number=index+1,
                    headline=post["headline"], paragraphs=post["paragraphs"],
                    column="\n\n".join(post["paragraphs"]),
                    scene_key=f"life_column_{index}", copy_version=VERSION,
                    context=f"月は{facts['moon']['sign']}")
    return None
