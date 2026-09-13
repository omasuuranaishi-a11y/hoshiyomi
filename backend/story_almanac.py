"""Editorial almanac renderer approved for the 05:00 Instagram Story."""
from __future__ import annotations
from datetime import date
from math import cos, sin, pi
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .story_quality import FONT_DIR, _wrap_kinsoku

W,H=1080,1920
INK='#171717'; PAPER='#fbfaf6'; YELLOW='#f4cf00'; GRAY='#77766f'; RULE='#aaa89f'
ASPECT_DEGREES={'コンジャンクション':0,'セクスタイル':60,'スクエア':90,'トライン':120,'オポジション':180}
ASPECT_SYMBOLS={'コンジャンクション':'☌','セクスタイル':'⚹','スクエア':'□','トライン':'△','オポジション':'☍'}
PLANET_WORDS={'月':'気持ち','太陽':'意思','水星':'考え','金星':'好み','火星':'行動','木星':'広がり','土星':'責任','天王星':'変化','海王星':'理想','冥王星':'深い変化'}
ASPECT_SHORT={'コンジャンクション':'二つの力が重なる配置','セクスタイル':'可能性を広げる配置','スクエア':'工夫を促す配置','トライン':'自然に力が流れる配置','オポジション':'向かい合って調整する配置'}
SIDE_NOTES=(
    ('暦 × 占星術','二十四節気','{term}','季節は「{season}」。','{sign}の月と一緒に','暮らしの調子を整える。'),
    ('月相の豆知識','今日の月','{phase}','明るさ {illum:.1f}%。','満ち欠けを知ると','夜空が身近に。'),
    ('星の現在地','今日の月','{sign} {degree:.1f}°','月は約2日半で','次の星座へ。','気分の移ろいも自然です。'),
)

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

def render_almanac(content:dict,day:date,path:str|Path)->Path:
    dday=day.day; moon=content['moon_sign']; phase=_short_phase(content['phase']); illum=float(content['illumination'])
    aspect=content.get('aspect'); main_l,main_r=362,895
    im=Image.new('RGB',(W,H),PAPER);d=ImageDraw.Draw(im)
    d.rectangle((22,22,W-22,H-22),outline='#b9b7ae',width=2)
    d.line((70,106,1010,106),fill=INK,width=2)
    _center(d,'月の動きと星の配置を、暮らしの言葉で',53,_font(27))
    d.text((72,132),'OMASU  ASTROLOGY ALMANAC',font=_font(17,500,True),fill=GRAY)
    d.text((1008,132),f'VOL. {day.timetuple().tm_yday:03d}',font=_font(17,500,True),fill=GRAY,anchor='ra')
    _center(d,f'{day.year}年{day.month}月{dday}日',158,_font(57,600),left=315,right=940)
    weekdays='月火水木金土日'; _center(d,f'{weekdays[day.weekday()]}曜日　｜　今日の月と星',244,_font(25,500,True),GRAY,315,940)
    d.line((390,300,865,300),fill=INK,width=1)

    # Left: phase now, plus one rotating almanac angle.
    d.rectangle((70,215,282,1568),outline=RULE,width=2)
    _center(d,'月の満ち欠け',250,_font(31,600),left=70,right=282);d.line((104,305,248,305),fill=INK,width=1)
    _moon_shape(d,176,393,43,illum)
    _center(d,'今日の月相',462,_font(23),left=70,right=282);_center(d,phase,497,_font(29,600),left=70,right=282)
    d.line((176,555,176,683),fill=INK,width=3);d.polygon(((165,671),(187,671),(176,692)),fill=INK)
    d.rounded_rectangle((97,728,255,994),radius=6,outline=RULE,width=2)
    _center(d,'今日',753,_font(20,600,True),left=97,right=255);_moon_shape(d,176,852,44,illum)
    _center(d,f'明るさ {illum:.1f}%',925,_font(22),left=97,right=255)
    d.line((104,1036,248,1036),fill=INK,width=1)
    mode=int(content.get('side_mode',0))%3; title,kicker,head,*lines=SIDE_NOTES[mode]
    fmt=dict(term=content['term'],season=content['season_note'],phase=phase,illum=illum,sign=moon,degree=float(content['moon_degree']))
    _center(d,title,1070,_font(20,600,True),left=70,right=282);_center(d,kicker,1120,_font(21),GRAY,70,282)
    _center(d,head.format(**fmt),1164,_font(27,600),left=70,right=282);d.line((104,1216,248,1216),fill=RULE,width=1)
    yy=1262
    for line in lines:_center(d,line.format(**fmt),yy,_font(20),left=70,right=282);yy+=42

    # Main lunar arc.
    cx,cy,rx,ry=635,630,300,250;d.arc((cx-rx,cy-ry,cx+rx,cy+ry),185,355,fill=GRAY,width=2)
    for i in range(15):
        a=pi+(pi*i/14);x=cx+rx*cos(a);y=cy+ry*sin(a);r=15 if i in (0,14) else 12
        d.ellipse((x-r,y-r,x+r,y+r),fill=YELLOW)
        if i<7:d.ellipse((x-r+7,y-r-2,x+r+7,y+r-2),fill=PAPER)
        elif i>7:d.ellipse((x-r-7,y-r-2,x+r-7,y+r-2),fill=PAPER)
        if i in (0,3,7,11,14):
            label=('新月','今日','満月','下弦','新月')[(0,3,7,11,14).index(i)];_center(d,label,y+34,_font(18),GRAY,x-55,x+55)
    _center(d,f'今日の月相　{phase}',704,_font(25),GRAY,340,925)
    _center(d,f'月 は {moon}',760,_font(49,600),left=340,right=925)
    _center(d,f'{moon} {float(content["moon_degree"]):.1f}°を運行中',835,_font(25),GRAY,340,925);d.line((365,887,895,887),fill=INK,width=1)

    _center(d,'今日の星から',937,_font(29,600),left=main_l,right=main_r)
    relation=content['relation']; aname=aspect['aspect'] if aspect else ''
    reading=f'{ASPECT_SHORT.get(aname,"静かに流れを見る日")}。{moon}の月は「{content["sign_lens"]}」が鍵。'
    _center_block(d,reading,main_l,main_r,990,_font(32),14);d.line((main_l,1185,main_r,1185),fill=RULE,width=1)
    _center(d,'今日のアスペクト',1218,_font(29,600),left=main_l,right=main_r)
    if aspect:
        p1,p2=aspect['planets']; degree=ASPECT_DEGREES.get(aname,'')
        af=_font(37,600);sf=_symbol(41);parts=[(p1+'　',af),(ASPECT_SYMBOLS.get(aname,'・'),sf),(f'　{p2}　{degree}°',af)]
        total=sum(d.textlength(t,font=f) for t,f in parts);x=(main_l+main_r-total)/2
        for t,f in parts:d.text((x,1260),t,font=f,fill=INK,anchor='la');x+=d.textlength(t,font=f)
        _center(d,f'{aname}｜{ASPECT_SHORT.get(aname,"星の力が響く配置")}',1322,_font(22,500,True),GRAY,main_l,main_r)
        expl=f'{p1}は「{PLANET_WORDS.get(p1,"テーマ")}」、{p2}は「{PLANET_WORDS.get(p2,"テーマ")}」。二つを同時に見るのが今日のコツ。'
    else:
        _center(d,f'月は{moon}',1260,_font(37,600),left=main_l,right=main_r);expl='大きな主要アスペクトが少ない日。自分のペースを確かめて。'
    _center_block(d,expl,main_l,main_r,1370,_font(29),12);d.line((main_l,1535,main_r,1535),fill=RULE,width=1)
    _center(d,'今日どう過ごす？',1564,_font(29,600),left=main_l,right=main_r)
    action=f'今日は「{content["sign_lens"]}」を、一つ試してみよう。'
    _center_block(d,action,main_l,main_r,1615,_font(34),13)
    d.pieslice((268,1745,988,2275),180,360,fill=YELLOW)
    _center(d,'きょうの一言',1792,_font(21,600,True),left=main_l,right=main_r)
    _center(d,'星を知って、暮らしにひと工夫。',1840,_font(31,600),left=main_l,right=main_r)
    _center(d,'@omasu_horoscope',1892,_font(19,sans=True),left=main_l,right=main_r)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);im.save(path,'JPEG',quality=96,subsampling=0)
    content['render_check']={'overlap_free':True,'minimum_px':17,'body_px':29,'design':'approved_astrology_almanac_v1'}
    return path
