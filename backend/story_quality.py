from __future__ import annotations

"""Deterministic high-fidelity renderer based on the approved designs."""

from datetime import date
import os
from pathlib import Path
from typing import Any, Iterable
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

WIDTH, HEIGHT = 1080, 1920
ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT / "assets" / "reference"
FONT_DIR = ROOT / "assets" / "fonts"
PAPER=(249,245,235); INK=(14,39,64); NAVY=(4,44,73); JADE=(24,119,117)
CORAL=(235,111,86); GOLD=(181,139,70); WHITE=(255,253,247); MUTED=(91,91,85)
THEMES = (
    ("珊瑚の朝", (238,119,92), (21,102,96), (186,145,73)),
    ("翡翠の庭", (43,126,111), (231,128,98), (197,161,91)),
    ("藍の星空", (15,58,88), (205,153,106), (228,190,113)),
    ("藤の余韻", (142,121,164), (54,112,105), (211,157,105)),
    ("金色の暦", (195,151,72), (25,91,83), (226,117,87)),
    ("水明の青", (68,122,145), (222,132,103), (178,152,102)),
    ("茜の宵", (166,76,78), (33,83,91), (216,166,101)),
)
SLOT_OFFSETS={"morning":0,"noon":2,"evening":4,"night":6}

def design_variant(day:date,slot:str)->dict[str,Any]:
    index=(day.toordinal()+SLOT_OFFSETS[slot])%len(THEMES)
    name,primary,secondary,gold=THEMES[index]
    return {"index":index,"name":name,"primary":primary,"secondary":secondary,"gold":gold}

def _decorate(im:Image.Image,day:date,slot:str)->Image.Image:
    theme=design_variant(day,slot);primary=theme["primary"];secondary=theme["secondary"];gold=theme["gold"]
    im=Image.blend(im,Image.new("RGB",im.size,primary),0.035)
    d=ImageDraw.Draw(im,"RGBA");v=theme["index"]
    if v==0:
        d.line((30,35,1050,35),fill=(*gold,190),width=3);d.line((30,1885,1050,1885),fill=(*gold,190),width=3)
    elif v==1:
        for x,y in ((70,120),(1000,230),(950,1740),(120,1810)):
            d.ellipse((x-6,y-6,x+6,y+6),fill=(*gold,220));d.line((x-18,y,x+18,y),fill=(*gold,180),width=2);d.line((x,y-18,x,y+18),fill=(*gold,180),width=2)
    elif v==2:
        d.arc((-120,1380,360,1940),270,70,fill=(*secondary,190),width=6)
        for i in range(6):
            y=1580+i*45;d.ellipse((55+i*16,y,105+i*16,y+25),fill=(*secondary,120))
    elif v==3:
        d.arc((750,-180,1220,390),80,220,fill=(*primary,180),width=8)
        for i in range(7):d.ellipse((865+i*24,115+i*9,873+i*24,123+i*9),fill=(*gold,200))
    elif v==4:
        d.polygon(((0,0),(190,0),(110,155),(0,210)),fill=(*primary,75));d.polygon(((1080,1920),(850,1920),(930,1755),(1080,1690)),fill=(*secondary,70))
    elif v==5:
        points=((70,220),(115,180),(155,245),(205,205),(250,270));d.line(points,fill=(*gold,180),width=2)
        for x,y in points:d.ellipse((x-5,y-5,x+5,y+5),fill=(*gold,220))
    else:
        import math
        cx,cy=970,145
        for angle in range(0,360,30):
            x2=cx+int(62*math.cos(math.radians(angle)));y2=cy+int(62*math.sin(math.radians(angle)));d.line((cx,cy,x2,y2),fill=(*gold,145),width=2)
        d.ellipse((cx-22,cy-22,cx+22,cy+22),fill=(*gold,120))
    return im


def _font_path() -> str:
    candidates: Iterable[Path | str] = (
        Path(os.getenv("STORY_SERIF_FONT_PATH", "")),
        FONT_DIR / "NotoSerifJP-VF.ttf",
        "C:/Windows/Fonts/NotoSerifJP-VF.ttf",
        "C:/Windows/Fonts/yumin.ttf",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    )
    for candidate in candidates:
        if str(candidate) and Path(candidate).is_file():
            return str(candidate)
    from .story_renderer import resolve_font_path
    return resolve_font_path()

def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_font_path(), size=size)

def _master(name: str) -> Image.Image:
    path = REFERENCE / name
    if not path.is_file():
        raise RuntimeError(f"Approved story master is missing: {path}")
    image = Image.open(path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return ImageEnhance.Sharpness(image).enhance(1.08)

def _wrap(draw, text, font, width):
    lines=[]; current=""
    for char in str(text):
        if char=="\n":
            lines.append(current); current=""; continue
        trial=current+char
        if current and draw.textlength(trial,font=font)>width:
            lines.append(current); current=char
        else: current=trial
    if current or not lines: lines.append(current)
    return lines

def _fit(draw, text, box, *, max_size, min_size=22, fill=INK, align="left", line_gap=.48):
    x1,y1,x2,y2=box
    for size in range(max_size,min_size-1,-2):
        font=_font(size); lines=_wrap(draw,text,font,x2-x1)
        ascent,descent=font.getmetrics(); gap=int(size*line_gap); line_h=ascent+descent+gap
        if len(lines)*line_h-gap<=y2-y1:
            y=y1
            for line in lines:
                length=draw.textlength(line,font=font)
                x=x1 if align=="left" else (x1+x2-length)/2
                draw.text((x,y),line,font=font,fill=fill); y+=line_h
            return size
    raise ValueError(f"Story text does not fit approved layout: {str(text)[:80]}")

def _center(draw,text,y,size,*,fill=INK,left=0,right=WIDTH):
    font=_font(size); x=left+(right-left-draw.textlength(text,font=font))/2
    draw.text((x,y),text,font=font,fill=fill)

def _box(draw,box,fill=PAPER): draw.rectangle(box,fill=fill)

def _date_text(day):
    wd=("MON","TUE","WED","THU","FRI","SAT","SUN")
    return f"{day.year}.{day.month}.{day.day}  {wd[day.weekday()]}"

def _render_morning(c:dict[str,Any],day:date)->Image.Image:
    im=_master("morning-approved.png"); d=ImageDraw.Draw(im)
    _box(d,(265,335,815,456),(249,245,234)); _center(d,_date_text(day),367,38,left=250,right=830)
    for x in range(320,760,10): d.ellipse((x,438,x+3,441),fill=INK)
    _center(d,"✶",420,22,fill=GOLD)
    _box(d,(130,615,725,824),(250,247,238))
    _fit(d,f"二十四節気｜{c['term']}",(145,630,720,712),max_size=47)
    d.line((145,738,660,738),fill=JADE,width=2)
    _fit(d,"季節の変化を、暮らしの小さな目印に。",(145,766,720,825),max_size=27,min_size=23)
    _box(d,(777,540,916,720),(247,243,231))
    _center(d,day.strftime("%B").upper(),550,20,fill=(51,97,73),left=770,right=925)
    _center(d,str(day.day),590,62,fill=(51,97,73),left=770,right=925)
    _center(d,day.strftime("%a").upper(),667,23,fill=(51,97,73),left=770,right=925)
    d.rounded_rectangle((112,1070,744,1283),radius=12,fill=NAVY)
    _fit(d,f"{c['phase']}｜明るさ {c['illumination']:.1f}%",(135,1085,735,1150),max_size=33,min_size=26,fill=WHITE)
    d.line((135,1170,690,1170),fill=GOLD,width=2)
    _fit(d,c["moon_line"],(135,1191,735,1275),max_size=28,min_size=23,fill=WHITE)
    _box(d,(165,1453,925,1608),(250,247,238))
    _fit(d,c["hint"],(195,1468,900,1592),max_size=43,min_size=31,align="center")
    _box(d,(170,1640,920,1715),(250,247,238))
    _fit(d,f"今日の問い｜{c['question']}",(188,1654,905,1707),max_size=27,min_size=22,align="center")
    return im

def _render_noon(c:dict[str,Any],day:date)->Image.Image:
    im=Image.new("RGB",(WIDTH,HEIGHT),PAPER); d=ImageDraw.Draw(im)
    d.rounded_rectangle((28,28,1052,1892),radius=62,fill=(251,244,229),outline=GOLD,width=2)
    d.polygon(((28,28),(360,28),(250,255),(28,330)),fill=CORAL)
    d.polygon(((790,28),(1052,28),(1052,320),(925,250)),fill=(217,157,174))
    d.polygon(((28,1650),(230,1760),(320,1892),(28,1892)),fill=(77,122,91))
    d.polygon(((1052,1640),(860,1730),(790,1892),(1052,1892)),fill=(221,177,103))
    _center(d,"12星座のセルフケア",100,25,fill=MUTED); _center(d,c["title"],165,58)
    _fit(d,c["lead"],(120,270,960,370),max_size=28,min_size=23,fill=MUTED,align="center")
    colors=((CORAL,"火","牡羊座・獅子座・射手座"),((78,124,91),"地","牡牛座・乙女座・山羊座"),((129,113,151),"風","双子座・天秤座・水瓶座"),((78,114,146),"水","蟹座・蠍座・魚座"))
    for index,((color,element,signs),key) in enumerate(zip(colors,("火","地","風","水"))):
        col,row=index%2,index//2; x,y=85+col*485,440+row*520
        d.rounded_rectangle((x,y,x+425,y+440),radius=34,fill=WHITE,outline=color,width=4)
        d.rectangle((x,y,x+425,y+86),fill=color)
        _center(d,f"{element}の星座",y+17,32,fill=WHITE,left=x,right=x+425)
        _center(d,signs,y+112,21,fill=MUTED,left=x+15,right=x+410)
        d.ellipse((x+157,y+165,x+267,y+275),outline=color,width=4)
        d.line((x+180,y+250,x+245,y+190),fill=color,width=3); d.ellipse((x+200,y+208,x+226,y+234),fill=color)
        _fit(d,c["actions"][key],(x+42,y+305,x+383,y+407),max_size=31,min_size=23,align="center")
    d.rounded_rectangle((90,1510,990,1730),radius=28,fill=(255,248,237),outline=CORAL,width=2)
    _fit(d,c["footer"],(145,1570,935,1687),max_size=35,min_size=27,align="center")
    _center(d,f"{day.year}.{day.month}.{day.day}  @omasu_horoscope",1805,23,fill=MUTED)
    return im

def _render_evening(c:dict[str,Any],day:date)->Image.Image:
    im=_master("evening-approved.png"); d=ImageDraw.Draw(im)
    _box(d,(805,42,1028,102),(249,245,235)); _fit(d,_date_text(day),(805,48,1025,90),max_size=18,min_size=16,align="center")
    d.rounded_rectangle((338,425,982,511),radius=10,fill=JADE)
    _fit(d,c["headline"],(365,438,955,500),max_size=37,min_size=28,fill=WHITE,align="center")
    _box(d,(430,586,955,755),(249,245,235)); _fit(d,"星の状態",(430,590,930,646),max_size=35)
    d.line((430,660,940,660),fill=NAVY,width=2)
    _fit(d,f"{c['sky']}｜{c['context']}",(440,684,930,805),max_size=25,min_size=18)
    _box(d,(430,850,955,1080),(249,245,235)); _fit(d,"心の傾向",(430,854,930,910),max_size=35)
    d.line((430,926,940,926),fill=NAVY,width=2)
    _fit(d,f"{c['tendency']}。\n{c['adjust']}。",(440,952,930,1070),max_size=26,min_size=21)
    _box(d,(430,1190,940,1450),(250,247,239)); _fit(d,"今夜の3分メンテ",(430,1192,910,1250),max_size=34,fill=JADE)
    y=1282
    for action in c["actions"]:
        d.ellipse((438,y+12,449,y+23),fill=(208,157,113))
        _fit(d,action,(465,y,915,y+48),max_size=24,min_size=20); y+=64
    d.rectangle((205,1510,1080,1773),fill=NAVY)
    _fit(d,c["footer"],(275,1560,1010,1725),max_size=35,min_size=27,fill=WHITE,align="center")
    return im

def _render_night(c:dict[str,Any],day:date)->Image.Image:
    im=_master("night-column-approved.png"); d=ImageDraw.Draw(im)
    _box(d,(570,180,725,242),(249,246,238)); _center(d,str(c["number"])[-2:],189,22,left=570,right=725)
    _box(d,(80,330,1000,445),(249,246,238)); _fit(d,c["headline"],(95,345,985,425),max_size=53,min_size=38,align="center")
    _box(d,(90,500,995,1585),(249,246,238))
    _fit(d,"\n\n".join(c["paragraphs"]),(125,515,955,1550),max_size=31,min_size=24,line_gap=.58)
    _box(d,(125,1625,955,1707),(249,246,238)); d.rectangle((125,1625,955,1707),outline=NAVY,width=2)
    _fit(d,c["ending"],(145,1640,935,1693),max_size=30,min_size=24,fill=NAVY,align="center")
    return im

def render_approved_story(content:dict[str,Any],day:date,output_path:str|Path)->Path:
    renderer={"morning":_render_morning,"noon":_render_noon,"evening":_render_evening,"night":_render_night}[content["slot"]]
    image=_decorate(renderer(content,day),day,content["slot"])
    if image.size!=(WIDTH,HEIGHT): raise RuntimeError("Story must be exactly 1080x1920")
    path=Path(output_path); path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path,"JPEG",quality=96,optimize=True,subsampling=0)
    if path.stat().st_size<150_000: raise RuntimeError("Story quality check failed: output is unexpectedly small")
    return path
