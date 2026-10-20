"""User-approved four-program rollout. Content dates are JST dates."""
from datetime import date,timedelta
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = date(2026, 9, 7)
VERSION = "2026-09-20-almanac-v4"
HOROSCOPE_COPY_START = date(2026, 9, 30)
HOROSCOPE_COPY_VERSION = "2026-09-30-daily-life-v3"
HOROSCOPE_CLEAR_START = date(2026, 10, 21)
HOROSCOPE_CLEAR_VERSION = "2026-10-21-daily-clear-v4"
COLUMNS = json.loads((ROOT / "story_columns.json").read_text(encoding="utf-8"))
DICTIONARY = json.loads((ROOT / "story_dictionary.json").read_text(encoding="utf-8"))
SIGN_NAMES = ("牡羊座","牡牛座","双子座","蟹座","獅子座","乙女座","天秤座","蠍座","射手座","山羊座","水瓶座","魚座")
LEGACY_HOUSE_OPENINGS = ("自分らしさが主役。","手持ちの良さを発見。","会話に新しいヒント。","居場所に心を向けて。","好きなことが入口。","いつもの流れに工夫。","対話で視点が広がる。","信頼を育てる時間。","好奇心が次の扉に。","積み重ねが形になる。","仲間との話に可能性。","静かな時間が充電に。")
LEGACY_HOUSE_ACTIONS = (
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

# From September 30 onward, each sign gets a clear reason or daily tendency
# followed by one concrete action. Five actions per house keep the sheet fresh
# while preserving the approved two-line layout.
HOUSE_OPENINGS = (
 "意思が輪郭を持つ日。","価値観を見直す日。","対話が展開を生む日。",
 "居場所が心を整える。","喜びが活力になる。","調整が効率を高める。",
 "対話が均衡を戻す。","共有が負担を分ける。","未知が視野を広げる。",
 "積み重ねが実を結ぶ。","協力が可能性を拓く。","余白が感覚を整える。",
)
HOUSE_ACTIONS = (
 ("装いを一つ更新する。","無理な依頼は断る。","姿勢を正して始める。","好みを判断基準に。","希望を先に共有する。"),
 ("在庫を見てから買う。","財布の中を整える。","手持ちで代用する。","固定費を一つ点検。","購入前に用途を確認。"),
 ("未返信を一件返す。","会いたい人へ連絡。","予定を簡潔に共有。","疑問を一つ調べる。","伝言を今日中に送る。"),
 ("机の上だけ整える。","玄関を三分整える。","家族と予定を確認。","部屋の空気を替える。","帰宅後の席を整える。"),
 ("趣味に10分使う。","好きな曲を一曲聴く。","写真を一枚残す。","創作を少し進める。","笑える作品を選ぶ。"),
 ("予定を一つ減らす。","水分を先に補う。","五分座って休む。","手順を一つ省く。","就寝時刻を決める。"),
 ("依頼は要点を明確に。","相手の話を聞き切る。","返答期限を共有する。","希望を具体的に示す。","誤解は会話で解く。"),
 ("信頼できる人に話す。","借りた物を今日返す。","家計の共有を確認。","一つだけ人に頼る。","重要な話は急がない。"),
 ("記事を一つ読む。","帰路を少し変える。","言葉を一つ調べる。","本を五分だけ開く。","休日案を一つ書く。"),
 ("完了した仕事を報告。","成果を三つ記録する。","後回しを一つ終える。","今日の成果を一行に。","明日の準備を一つ。"),
 ("案を一人へ送る。","相談相手を決める。","誘いには素直に返答。","話題を一つ提案する。","支援が必要と伝える。"),
 ("就寝前は何もしない。","通知を一時間切る。","温かい飲み物で休む。","一人で10分休む。","今日は早めに休む。")
)


# Approved October 21 sample: familiar situations and one concrete action.
# Keep earlier versions intact, and rotate five actions within each daily theme.
CLEAR_HOUSE_OPENINGS = (
 "自分の希望が見える。","出費を見直したい日。","連絡が増えそうな日。",
 "家のことが気になる。","気分転換をしたい日。","予定を詰めやすい日。",
 "話がすれ違いやすい。","負担が偏りやすい。","調べると糸口がある。",
 "小さな成果が出そう。","相談すると進みそう。","考えすぎて疲れそう。",
)
CLEAR_HOUSE_ACTIONS = (
 ("できる範囲を伝える。","希望の時間を伝える。","行きたい店を提案。","今日は無理と伝える。","自分の予定も確認。"),
 ("買う前に在庫確認。","定期購入を確認。","使わない物を整理。","買う物をメモする。","支出を一つ記録。"),
 ("日時を確かめて返信。","未返信を一件返す。","予定の変更を連絡。","用件を分けて伝える。","会う場所を確認。"),
 ("机の上を片づける。","玄関の靴をそろえる。","寝る前に洗い物を。","家族と予定を確認。","帰宅後は部屋で休む。"),
 ("好きな曲でひと息。","昼休みに少し散歩。","好きな本を五分読む。","趣味に10分使う。","気になる映画を選ぶ。"),
 ("休憩も予定に入れる。","急がない用事は明日。","移動の時間も計算。","空き時間を一つ残す。","終える時刻を決める。"),
 ("聞いた内容を確認。","金額と期限を確認。","約束をメモに残す。","結論を先に伝える。","不明な点は聞き直す。"),
 ("家事を一つ頼む。","一人で悩まず相談。","共有の費用を確認。","役割分担を話す。","頼める用事を分ける。"),
 ("気になる言葉を検索。","手順を一度読み直す。","詳しい人に聞く。","説明書を開いて確認。","別の方法も調べる。"),
 ("済んだ仕事を報告。","終えた用事を記録。","できた事を一つ書く。","進んだ所まで共有。","片づいた場所を保つ。"),
 ("詳しい人に相談を。","困った点を一つ話す。","相談できる人へ連絡。","同僚に手順を聞く。","友人に意見を聞く。"),
 ("通知を切ってひと息。","寝る前はスマホ休み。","温かい飲み物で休む。","考え事を紙に書く。","今日は早めに床へ。"),
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
    if day >= HOROSCOPE_CLEAR_START:
        openings,actions=CLEAR_HOUSE_OPENINGS,CLEAR_HOUSE_ACTIONS
        action_index=(day-HOROSCOPE_CLEAR_START).days%len(actions[0])
        copy_version=HOROSCOPE_CLEAR_VERSION
    elif day >= HOROSCOPE_COPY_START:
        openings,actions=HOUSE_OPENINGS,HOUSE_ACTIONS
        action_index=(day-HOROSCOPE_COPY_START).days%len(actions[0])
        copy_version=HOROSCOPE_COPY_VERSION
    else:
        openings,actions=LEGACY_HOUSE_OPENINGS,LEGACY_HOUSE_ACTIONS
        action_index=mode
        copy_version=VERSION
    items=[]
    for index,sign in enumerate(SIGN_NAMES):
        house=(moon_index-index)%12+1
        action=actions[house-1][action_index]
        items.append({"sign":sign,"house":house,"text":openings[house-1]+action,"element":index%4})
    return dict(slot="noon",content_kind="horoscope_20260907",title="12星座 きょうの運勢",items=items,
                moon_sign=facts["moon"]["sign"],scene_key="daily_twelve_signs",
                copy_version=copy_version,
                method="太陽星座を第1の領域とするサイン単位の一般向け解釈。出生時刻による個人ハウスではない。",
                source_positions=facts["positions"],source_aspects=aspects,reading_hour_jst=5)


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
        return dict(slot=slot,content_kind="almanac_20260914",title="今日の月と星",term=term,
                    season_note=SEASON_NOTES[term],phase=phase['name'],illumination=phase['illumination_percent'],
                    moon_sign=moon['sign'],moon_degree=moon.get('degree_in_sign',0.0),moon_line=f"月は{ing['from']}から、{ing['local_time']}ごろ{ing['to']}へ。" if ing else f"月は一日を通して{moon['sign']}にいます。",
                    aspect=aspect,relation=relation,sign_lens=sign_lens,
                    hint=sky+relation+f"月が{moon['sign']}の今日は、{sign_lens}ことにも目を向けて。",
                    thinking=actions[(day-START).days%len(actions)],side_mode=0,
                    scene_key=f"almanac_{(day-START).days%21}",copy_version=VERSION)
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
