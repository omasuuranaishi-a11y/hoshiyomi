from __future__ import annotations
from datetime import date
import hashlib
from pathlib import Path
from typing import Any
from PIL import Image,ImageDraw
from .story_renderer import WIDTH,HEIGHT,_font,_wrap_text,resolve_font_path

SLOTS=("morning","noon","evening","night")
PAPER=(248,243,232);INK=(18,43,68);NAVY=(5,42,70);JADE=(36,116,111);CORAL=(232,115,91);APRICOT=(240,177,119);LAV=(194,184,211);GOLD=(190,148,72);WHITE=(255,253,247);MUTED=(92,91,86)
ELEMENT={"牡羊座":"火","獅子座":"火","射手座":"火","牡牛座":"地","乙女座":"地","山羊座":"地","双子座":"風","天秤座":"風","水瓶座":"風","蟹座":"水","蠍座":"水","魚座":"水"}
GROUPS={"火":"牡羊座・獅子座・射手座","地":"牡牛座・乙女座・山羊座","風":"双子座・天秤座・水瓶座","水":"蟹座・蠍座・魚座"}
ACTIONS={
"火":("5分だけ体を動かす","気になることを一つ始める","胸を開いて深呼吸する","短い散歩で熱を逃がす","やることを一つに絞る","好きな音楽を一曲聴く","迷う前に小さく試す","肩を回して力を抜く"),
"地":("机の上を一つ整える","温かいものをゆっくり飲む","足裏の感覚を確かめる","明日の持ち物を一つ準備","予定を八割に減らす","目の前の一か所を拭く","食事を座って味わう","終えたことに丸をつける"),
"風":("気持ちを三行だけ書く","返事の前に一呼吸置く","窓を開けて空気を入れ替える","考えを声に出して整理する","通知を10分だけ閉じる","問いを一つ紙に置く","誰かに短い言葉で伝える","情報を一つ手放す"),
"水":("一人で静かな時間をとる","手を温めて呼吸を数える","湯船で感情をほどく","無理な共感から少し離れる","好きな香りを一つ選ぶ","涙や沈黙を急いで止めない","安心できる場所に戻る","今の気分に名前をつける")}
TEND={
"牡羊座":("急いで答えを出したくなる","勢いを、小さな着手に変える"),"牡牛座":("慣れた安心を守りたくなる","五感が落ち着く順番を選ぶ"),"双子座":("考えと言葉が増えやすい","情報を一度、外へ書き出す"),"蟹座":("周りの気持ちを抱えやすい","自分の安心を先に確かめる"),"獅子座":("自分らしく表したくなる","人の評価より納得を選ぶ"),"乙女座":("足りない所に目が向きやすい","反省ではなく調整に使う"),"天秤座":("正解の間で揺れやすい","両方が少し楽な形を探す"),"蠍座":("一つのことを深く考えやすい","本音を一行だけ言葉にする"),"射手座":("遠くへ気持ちが向かいやすい","今日の一歩に好奇心を戻す"),"山羊座":("結果と責任を背負いやすい","続けられる量まで小さくする"),"水瓶座":("いつもの形に窮屈さを感じる","やり方を一つだけ変えてみる"),"魚座":("境界がやわらかくなりやすい","感じる時間と休息を分ける")}
ZEN=(("答えを急がない夜","余計な動きを止める"),("握りしめない練習","変わっていくものを追いかけない"),("足りないものを数えない","すでにあるものへ視線を戻す"),("心を静かに眺める","良し悪しを決めず、ただ気づく"),("真ん中へ戻る夜","頑張りすぎと諦めの間を選ぶ"),("手放すのは、負けではない","役目を終えた考えを下ろす"),("今日を今日のまま閉じる","未完成を責めずに眠りへ渡す"),("静けさは、つくるものではない","重ねた判断を一枚ずつ外す"))

def _seed(day,slot):return int(hashlib.sha256(f"{day}:{slot}".encode()).hexdigest()[:12],16)
def _pick(seq,seed,n=0):return seq[(seed*17+n*13)%len(seq)]
def solar_term(facts):
    sun=next(x for x in facts["positions"] if x["planet"]=="太陽")
    names={0:"春分",15:"清明",30:"穀雨",45:"立夏",60:"小満",75:"芒種",90:"夏至",105:"小暑",120:"大暑",135:"立秋",150:"処暑",165:"白露",180:"秋分",195:"寒露",210:"霜降",225:"立冬",240:"小雪",255:"大雪",270:"冬至",285:"小寒",300:"大寒",315:"立春",330:"雨水",345:"啓蟄"}
    return names[(int(sun["longitude"]//15)*15)%360]

def build_slot_content(facts:dict[str,Any],slot:str)->dict[str,Any]:
    if slot not in SLOTS:raise ValueError("unknown slot")
    day=date.fromisoformat(facts["target_date"]);seed=_seed(day,slot);moon=facts["moon"];phase=facts["moon_phase"];ing=facts.get("moon_ingress");aspect=(facts.get("major_aspects") or [None])[0]
    tendency,adjust=TEND[moon["sign"]];context=f"月は{moon['sign']} {moon['degree_in_sign']:.1f}度"+(f"。{ing['local_time']}ごろ{ing['to']}へ" if ing else "")
    if slot=="morning":
        line=f"月は{ing['from']}から、{ing['local_time']}ごろ{ing['to']}へ。" if ing else f"月は一日を通して{moon['sign']}にいます。"
        qs=("自分のために5分使うなら？","今日、少し軽くできることは？","整える前に、やめられることは？","今日の自分へ何を渡したい？","急がず育てたいことは？","心地よい順番に変えるなら？")
        return dict(slot=slot,title="きょうの暦と月",term=solar_term(facts),phase=phase["name"],illumination=phase["illumination_percent"],moon_line=line,hint=f"{adjust}。今日は、今できることをひとつ。",question=_pick(qs,seed))
    if slot=="noon":
        acts={e:_pick(ACTIONS[e],seed,i) for i,e in enumerate(("火","地","風","水"))}
        return dict(slot=slot,title="疲れた日の、戻り方",subtitle="12星座のセルフケア",lead=f"{context}。{tendency}日だから、元素別に小さく整えて。",actions=acts,footer="星を理由に頑張るより、星を休むきっかけに。")
    if slot=="evening":
        pool=ACTIONS[ELEMENT[moon["sign"]]];acts=[_pick(pool,seed,i+2) for i in range(3)];sky=f"{aspect['planets'][0]}と{aspect['planets'][1]}の{aspect['aspect']}" if aspect else f"{phase['name']}のリズム"
        return dict(slot=slot,title="星よみメンテナンス",headline=f"月が{moon['sign']}にいる夕方",sky=sky,context=context,tendency=tendency,adjust=adjust,actions=acts,footer=f"{moon['sign']}の月は、反省より『調整』に使う。\n明日の自分を助ける夕方に。")
    element=ELEMENT[moon["sign"]]
    headlines=(
        "感情は、結論ではない",
        "反応と選択のあいだ",
        "迷いは、止まる理由ではない",
        "整えるとは、減らすこと",
        "気分と事実を、分けてみる",
        "小さな違和感を、観察する",
        "正しさより、選び直せる余白",
        "考える前に、気づいてみる",
    )
    logic={
        "火":"動きたい気持ちは推進力。ただし、勢いと優先順位は別です。",
        "地":"整えたい気持ちは安定を求めるサイン。完璧さと必要十分は別です。",
        "風":"考えが増えるのは視点が動いている証拠。情報量と納得感は別です。",
        "水":"感情は、守りたいものを知らせる情報。気分と事実は別です。",
    }
    practices=(
        "すぐ反応せず、ひと呼吸おいて観察する。その小さな余白が、今日の選択を整えます。",
        "答えを急がず、いま起きていることを一度そのまま見る。気づきが、次の一手を静かにします。",
        "足す前に、ひとつ手放せるものを探す。余白ができると、本当に必要なことが見えてきます。",
        "良い悪いを決める前に、感情へ名前をつける。それだけで、反応は少し選択に変わります。",
    )
    endings=(
        "今日の視点｜反応の前に、ひと呼吸。",
        "今日の視点｜気分と事実を、分けてみる。",
        "今日の視点｜答えより、まず観察を。",
        "今日の視点｜足す前に、ひとつ減らす。",
    )
    astrology=f"月が{moon['sign']}を進む午前は、{tendency}。"
    paragraphs=[astrology,logic[element],_pick(practices,seed,1)]
    return dict(slot=slot,title="星と心のミニコラム",number=day.toordinal(),headline=_pick(headlines,seed),context=context,paragraphs=paragraphs,ending=_pick(endings,seed,2))

def _text(d,xy,text,font,fill=INK,width=None,gap=14):
    lines=_wrap_text(d,text,font,width) if width else text.splitlines();x,y=xy
    for line in lines:d.text((x,y),line,font=font,fill=fill);b=d.textbbox((x,y),line or "あ",font=font);y+=b[3]-b[1]+gap
    return y
def _header(d,day,fp,label):
    d.text((70,60),label,font=_font(fp,25),fill=MUTED);stamp=day.strftime("%Y.%m.%d  %a").upper();f=_font(fp,25);d.text((WIDTH-70-d.textlength(stamp,font=f),60),stamp,font=f,fill=MUTED);d.line((70,102,WIDTH-70,102),fill=GOLD,width=2)
def _footer(d,fp):
    s="@omasu_horoscope";f=_font(fp,27);d.text(((WIDTH-d.textlength(s,font=f))/2,1845),s,font=f,fill=MUTED)
def _morning(d,c,day,fp):
    d.polygon([(0,0),(250,0),(180,300),(0,360)],fill=CORAL);d.polygon([(810,0),(1080,0),(1080,500),(900,355)],fill=NAVY);d.polygon([(0,1650),(250,1510),(420,1920),(0,1920)],fill=JADE);_header(d,day,fp,"DAILY CALENDAR & MOON");_text(d,(165,165),c["title"],_font(fp,78),width=760)
    d.rounded_rectangle((85,410,995,800),34,fill=WHITE,outline=GOLD,width=2);d.rectangle((85,410,250,478),fill=JADE);d.text((122,423),"暦",font=_font(fp,36),fill=WHITE);d.text((135,525),f"二十四節気｜{c['term']}",font=_font(fp,50),fill=INK);_text(d,(135,625),"季節の小さな変化を、暮らしの目印に。",_font(fp,34),fill=MUTED,width=760)
    d.rounded_rectangle((85,845,995,1275),34,fill=NAVY);d.text((125,895),"月の満ち欠け",font=_font(fp,38),fill=LAV);d.text((125,980),f"{c['phase']}｜明るさ {c['illumination']:.1f}%",font=_font(fp,43),fill=WHITE);_text(d,(125,1085),c["moon_line"],_font(fp,36),fill=WHITE,width=780);d.ellipse((760,905,925,1070),fill=(245,218,150));d.ellipse((805,880,970,1045),fill=NAVY)
    d.rounded_rectangle((85,1320,995,1775),34,fill=WHITE,outline=CORAL,width=3);d.rectangle((85,1320,480,1390),fill=CORAL);d.text((125,1335),"星からの小さなヒント",font=_font(fp,32),fill=WHITE);_text(d,(135,1450),c["hint"],_font(fp,43),width=790);d.line((135,1625,945,1625),fill=CORAL,width=2);_text(d,(135,1650),f"今日の問い｜{c['question']}",_font(fp,32),width=800);_footer(d,fp)
def _noon(d,c,day,fp):
    d.polygon([(0,0),(1080,0),(1080,230),(0,340)],fill=CORAL);_header(d,day,fp,"12 SIGNS SELF CARE");d.text((80,150),c["subtitle"],font=_font(fp,34),fill=WHITE);d.text((80,215),c["title"],font=_font(fp,68),fill=WHITE);_text(d,(80,365),c["lead"],_font(fp,32),fill=MUTED,width=920);colors={"火":CORAL,"地":JADE,"風":LAV,"水":NAVY}
    for e,(x,y) in zip(("火","地","風","水"),[(70,555),(555,555),(70,1045),(555,1045)]):d.rounded_rectangle((x,y,x+455,y+420),38,fill=WHITE,outline=colors[e],width=4);d.ellipse((x+28,y+28,x+112,y+112),fill=colors[e]);d.text((x+53,y+43),e,font=_font(fp,37),fill=WHITE);_text(d,(x+32,y+140),GROUPS[e],_font(fp,25),fill=MUTED,width=390);_text(d,(x+32,y+235),c["actions"][e],_font(fp,39),width=390)
    d.rounded_rectangle((70,1515,1010,1775),34,fill=(252,231,219));_text(d,(120,1580),c["footer"],_font(fp,40),width=840);_footer(d,fp)
def _evening(d,c,day,fp):
    d.rectangle((0,0,220,HEIGHT),fill=NAVY);d.ellipse((40,140,180,280),fill=(245,219,151));d.ellipse((80,115,220,255),fill=NAVY);_header(d,day,fp,"EVENING ASTRO CARE");_text(d,(285,155),c["title"],_font(fp,67),width=700);d.rounded_rectangle((270,365,1015,460),18,fill=JADE);d.text((315,385),c["headline"],font=_font(fp,38),fill=WHITE);y=520
    for num,title,body in [("01","星の状態",f"{c['sky']}\n{c['context']}"),("02","心の傾向",f"{c['tendency']}。\n{c['adjust']}。")]:d.text((270,y),num,font=_font(fp,61),fill=NAVY);d.text((390,y+8),title,font=_font(fp,40),fill=INK);d.line((390,y+70,975,y+70),fill=GOLD,width=2);y=_text(d,(390,y+105),body,_font(fp,32),width=585)+55
    d.rounded_rectangle((245,1040,1015,1475),32,fill=WHITE,outline=APRICOT,width=3);d.text((270,1075),"03",font=_font(fp,61),fill=NAVY);d.text((390,1085),"今夜の3分メンテ",font=_font(fp,40),fill=JADE);y=1185
    for a in c["actions"]:d.ellipse((390,y+12,405,y+27),fill=APRICOT);y=_text(d,(430,y),a,_font(fp,32),width=520)+28
    d.rectangle((220,1530,1080,1785),fill=NAVY);_text(d,(285,1580),c["footer"],_font(fp,39),fill=WHITE,width=700);_footer(d,fp)
def _night(d,c,day,fp):
    d.ellipse((500,45,580,125),outline=GOLD,width=5);_header(d,day,fp,f"{c['title']}  {str(c['number'])[-3:]}");d.text((80,160),c["headline"],font=_font(fp,61),fill=INK);d.line((80,260,1000,260),fill=GOLD,width=2);d.text((80,295),c["context"],font=_font(fp,27),fill=JADE);y=380
    for p in c["paragraphs"]:y=_text(d,(92,y),p,_font(fp,31),width=895,gap=12)+28
    top=min(y+12,1640);d.rounded_rectangle((80,top,1000,min(top+130,1770)),8,outline=NAVY,width=2);f=_font(fp,34);d.text(((WIDTH-d.textlength(c["ending"],font=f))/2,min(y+48,1675)),c["ending"],font=f,fill=NAVY);_footer(d,fp)
def render_slot_story(content,day,output_path):
    from .story_quality import render_approved_story
    return render_approved_story(content,day,output_path)
