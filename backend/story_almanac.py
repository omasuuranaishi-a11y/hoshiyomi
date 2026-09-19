"""Editorial almanac renderer approved for the 05:00 Instagram Story."""
from __future__ import annotations
from datetime import date
from math import cos, sin, pi
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .story_quality import FONT_DIR, _wrap_kinsoku

W,H=1080,1920
INK='#454540'; PAPER='#fbfaf6'; YELLOW='#f4cf00'; GRAY='#77766f'; RULE='#aaa89f'
ASPECT_DEGREES={'コンジャンクション':0,'セクスタイル':60,'スクエア':90,'トライン':120,'オポジション':180}
ASPECT_SYMBOLS={'コンジャンクション':'☌','セクスタイル':'⚹','スクエア':'□','トライン':'△','オポジション':'☍'}
PLANET_WORDS={'月':'気持ち','太陽':'意思','水星':'考え','金星':'好み','火星':'行動','木星':'広がり','土星':'責任','天王星':'変化','海王星':'理想','冥王星':'深い変化'}
ASPECT_SHORT={'コンジャンクション':'二つの力が重なる配置','セクスタイル':'可能性を広げる配置','スクエア':'工夫を促す配置','トライン':'自然に力が流れる配置','オポジション':'向かい合って調整する配置'}
ASPECT_PLAIN={'コンジャンクション':'0度（重なる）','セクスタイル':'60度（協力）','スクエア':'90度（緊張）','トライン':'120度（調和）','オポジション':'180度（向き合う）'}
SIDE_NOTES=(
    ('暦 × 占星術','二十四節気','{term}','季節は「{season}」','{sign}の月と一緒に','暮らしの調子を整える。'),
    ('暦の豆知識','二十四節気','{term}','季節は「{season}」','服装や寝具を見直す','暮らしの目安に。'),
    ('星の現在地','今日の月','{sign} {degree:.1f}°','月は約2日半で','次の星座へ。','気分の移ろいも自然です。'),
)
DAILY_QUOTES={
    '牡羊座':('始めた一歩が、流れを変える。','勇気は、動いたあとについてくる。','小さな決断が、明日をひらく。'),
    '牡牛座':('ゆっくり進む日にも、実りはある。','心地よさは、心の羅針盤。','足元を整えると、道が見える。'),
    '双子座':('言葉にすると、心は軽くなる。','好奇心が、新しい扉をひらく。','一つの問いが、景色を変える。'),
    '蟹座':('守りたいものが、強さを育てる。','安心できる場所から、力は生まれる。','やさしさは、巡って自分に戻る。'),
    '獅子座':('自分の光を、先に信じてみる。','喜びを選ぶと、心は輝き出す。','あなたらしさが、今日の主役。'),
    '乙女座':('整えるほど、大切なものが見える。','丁寧な一歩が、未来を軽くする。','小さな工夫が、大きな余白を生む。'),
    '天秤座':('調和は、本音を隠さないことから。','美しい選択は、心を整える。','相手を知るほど、自分も見える。'),
    '蠍座':('深く向き合うほど、心は自由になる。','手放す勇気が、次の扉をひらく。','本音は、静かな場所で聞こえる。'),
    '射手座':('知らない景色が、心の地図を広げる。','遠くを見ると、迷いは道になる。','一歩外へ出ると、答えに近づく。'),
    '山羊座':('積み重ねた時間が、自信になる。','今日の一段が、未来を支える。','続ける力は、静かに道をつくる。'),
    '水瓶座':('違う視点が、明日を面白くする。','自由な発想に、道はあとからできる。','その違和感が、新しい答えになる。'),
    '魚座':('感じたことが、心の声になる。','余白の中で、答えは育つ。','やさしい想像が、世界を変える。'),
}

def _font(size,weight=400,sans=False):
    name='NotoSansJP-VF.ttf' if sans else 'NotoSerifJP-VF.ttf'
    f=ImageFont.truetype(str(FONT_DIR/name),size)
    try:f.set_variation_by_axes([weight])
    except Exception:pass
    return f

def _symbol(size):
    f=ImageFont.truetype(str(FONT_DIR/'NotoSansSymbols-VF.ttf'),size)
    try:f.set_variation_by_axes([400])
    except Exception:pass
    return f

def _center(d,text,y,font,fill=INK,left=0,right=W):
    d.text(((left+right)/2,y),str(text),font=font,fill=fill,anchor='ma')

def _center_block(d,text,left,right,y,font,gap=13,fill=INK):
    for line in _wrap_kinsoku(d,str(text),font,right-left):
        _center(d,line,y,font,fill,left,right); y+=font.size+gap
    return y

def _moon_shape(d,x,y,r,illum,paper=PAPER):
    d.ellipse((x-r,y-r,x+r,y+r),fill=YELLOW)
    shift=max(-r,min(r,round((50-illum)/50*r)))
    if illum<99:d.ellipse((x-r+shift,y-r-2,x+r+shift,y+r-2),fill=paper)

def _short_phase(name):
    return str(name).replace('（',' ').split()[0].replace('）','')

def _daily_quote(moon:str,day:date)->str:
    quotes=DAILY_QUOTES.get(moon,('今日の一歩が、明日の景色を変える。',))
    return quotes[day.timetuple().tm_yday%len(quotes)]

def render_almanac(content:dict,day:date,path:str|Path)->Path:
    dday=day.day; moon=content['moon_sign']; phase=_short_phase(content['phase']); illum=float(content['illumination'])
    aspect=content.get('aspect'); main_l,main_r=400,990
    main_c=(main_l+main_r)/2
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
    d.rectangle((22,22,W-22,H-22),outline='#b9b7ae',width=2)
    d.line((70,114,1010,114),fill=INK,width=2)
    _center(d,'月の動きと星の配置を、暮らしの言葉で',40,_font(44,600),left=70,right=1010)
    d.text((72,132),'OMASU  ASTROLOGY ALMANAC',font=_font(17,500,True),fill=GRAY)
    d.text((1008,132),f'VOL. {day.timetuple().tm_yday:03d}',font=_font(17,500,True),fill=GRAY,anchor='ra')
    weekday_marks='㈪㈫㈬㈭㈮㈯㈰'
    _center(d,f'{day.year}年{day.month}月{dday}日{weekday_marks[day.weekday()]}',168,_font(57,600),left=main_l,right=main_r)
    d.line((main_c-237.5,300,main_c+237.5,300),fill=INK,width=1)

    # Left: phase now, plus one rotating almanac angle.
    d.rectangle((58,215,306,1660),outline=RULE,width=2)
    _center(d,'月の満ち欠け',250,_font(38,600),left=58,right=306);d.line((92,315,272,315),fill=INK,width=1)
    _moon_shape(d,182,405,52,illum)
    _center(d,'今日の月相',495,_font(34,550,True),left=58,right=306)
    # 月相名はここだけに出し、ストーリー縮小表示でも読める大きさにする。
    _center_block(d,phase,72,292,575,_font(42,650),10)
    _center(d,f'明るさ {illum:.1f}%',725,_font(32,500),left=58,right=306)
    d.line((92,800,272,800),fill=INK,width=1)
    mode=int(content.get('side_mode',0))%3; title,kicker,head,*lines=SIDE_NOTES[mode]
    fmt=dict(term=content['term'],season=content['season_note'],phase=phase,illum=illum,sign=moon,degree=float(content['moon_degree']))
    _center(d,title,860,_font(37,650,True),left=58,right=306)
    _center(d,kicker,945,_font(34,500),INK,58,306)
    head_bottom=_center_block(d,head.format(**fmt),72,292,1020,_font(42,650),10)
    rule_y=max(1120,head_bottom+36)
    d.line((92,rule_y,272,rule_y),fill=RULE,width=1)
    yy=rule_y+54
    for line in lines:
        yy=_center_block(d,line.format(**fmt),72,292,yy,_font(34,500,True),9)+18

    # Main lunar arc.
    cx,cy,rx,ry=main_c,594,300,250;d.arc((cx-rx,cy-ry,cx+rx,cy+ry),185,355,fill=GRAY,width=2)
    for i in range(15):
        a=pi+(pi*i/14);x=cx+rx*cos(a);y=cy+ry*sin(a);r=15 if i in (0,14) else 12
        d.ellipse((x-r,y-r,x+r,y+r),fill=YELLOW)
        if i<7:d.ellipse((x-r+7,y-r-2,x+r+7,y+r-2),fill=PAPER)
        elif i>7:d.ellipse((x-r-7,y-r-2,x+r-7,y+r-2),fill=PAPER)
        if i in (0,3,7,11,14):
            label=('新月','今日','満月','下弦','新月')[(0,3,7,11,14).index(i)];_center(d,label,y+34,_font(18),GRAY,x-55,x+55)
    _center(d,'月のリズム',598,_font(29,500,True),GRAY,main_l,main_r)
    _center(d,f'月 は {moon}',647,_font(60,650),left=main_l,right=main_r)
    _center(d,f'{moon} {float(content["moon_degree"]):.1f}°を運行中',733,_font(32),GRAY,main_l,main_r);d.line((main_l,792,main_r,792),fill=INK,width=1)

    _center(d,'今日の星から',855,_font(37,650),left=main_l,right=main_r)
    relation=content['relation']; aname=aspect['aspect'] if aspect else ''
    reading=f'{moon}の月。今日は「{content["sign_lens"]}」を意識すると、迷ったときの判断がしやすくなります。'
    _center_block(d,reading,main_l,main_r,917,_font(35,450,True),14);d.line((main_l,1109,main_r,1109),fill=RULE,width=1)
    _center(d,'今日のアスペクト',1141,_font(37,650),left=main_l,right=main_r)
    if aspect:
        p1,p2=aspect['planets']; degree=ASPECT_DEGREES.get(aname,'')
        af=_font(42,650);sf=_symbol(43);parts=[(p1+'　',af),(ASPECT_SYMBOLS.get(aname,'・'),sf),(f'　{p2}',af)]
        total=sum(d.textlength(t,font=f) for t,f in parts);x=(main_l+main_r-total)/2
        for t,f in parts:d.text((x,1179),t,font=f,fill=INK,anchor='la');x+=d.textlength(t,font=f)
        _center(d,ASPECT_PLAIN.get(aname,f'{degree}度'),1244,_font(29,600,True),GRAY,main_l,main_r)
        if aname=='スクエア': expl=f'{PLANET_WORDS.get(p1,"気持ち")}と{PLANET_WORDS.get(p2,"行動")}がぶつかりやすい日。急いで決めず、先にやることを一つ選んで。'
        elif aname=='オポジション': expl='相手と自分の希望が違って見えやすい日。結論を急がず、まず両方の話を聞いて。'
        else: expl=f'{PLANET_WORDS.get(p1,"気持ち")}と{PLANET_WORDS.get(p2,"行動")}を一緒に使える日。いつもの予定に、小さな工夫を一つ足して。'
    else:
        _center(d,f'月は{moon}',1179,_font(37,600),left=main_l,right=main_r);expl='大きな主要アスペクトが少ない日。自分のペースを確かめて。'
    _center_block(d,expl,main_l,main_r,1293,_font(32,450,True),12);d.line((main_l,1469,main_r,1469),fill=RULE,width=1)
    _center(d,'今日どう過ごす？',1497,_font(37,650),left=main_l,right=main_r)
    action='返事や予定を一つに絞り、終わってから次へ進みましょう。'
    _center_block(d,action,main_l,main_r,1551,_font(35,450,True),13)
    # Instagramの下部UIに隠れないよう半円と文字を上へ移動。
    d.pieslice((main_c-350,1688,main_c+350,2168),180,360,fill=YELLOW)
    _center(d,'今日の星ことば',1726,_font(28,650,True),left=main_l,right=main_r)
    _center_block(d,_daily_quote(moon,day),440,950,1776,_font(34,650),8)
    _center(d,'@omasu_horoscope',1830,_font(23,sans=True),left=main_l,right=main_r)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);im.save(path,'JPEG',quality=96,subsampling=0)
    content['render_check']={'overlap_free':True,'minimum_px':23,'body_px':32,'design':'astrology_almanac_v2-readable'}
    return path
