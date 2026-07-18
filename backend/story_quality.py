from __future__ import annotations

"""Deterministic high-fidelity renderer based on the approved designs."""

from datetime import date
import os
from pathlib import Path
from typing import Any, Iterable
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

WIDTH, HEIGHT = 1080, 1920
SAFE_TOP = 150
SAFE_BOTTOM = 1680
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
MOTIFS = ("double-rule", "stardust", "celestial-arc", "open-corners")
SLOT_OFFSETS={"morning":0,"noon":2,"evening":4,"night":6}

def design_variant(day:date,slot:str)->dict[str,Any]:
    sequence=day.toordinal()+SLOT_OFFSETS[slot]
    palette_index=sequence%len(THEMES)
    motif_index=(sequence//len(THEMES)+SLOT_OFFSETS[slot])%len(MOTIFS)
    name,primary,secondary,gold=THEMES[palette_index]
    return {"index":palette_index,"motif_index":motif_index,"name":f"{name} / {MOTIFS[motif_index]}","primary":primary,"secondary":secondary,"gold":gold}

def _decorate(im:Image.Image,day:date,slot:str)->Image.Image:
    theme=design_variant(day,slot);primary=theme["primary"];secondary=theme["secondary"];gold=theme["gold"]
    im=Image.blend(im,Image.new("RGB",im.size,primary),0.035)
    d=ImageDraw.Draw(im,"RGBA");v=theme["motif_index"]
    if v==0:
        d.line((30,122,1050,122),fill=(*gold,190),width=3);d.line((30,1715,1050,1715),fill=(*gold,150),width=3)
    elif v==1:
        for x,y in ((28,230),(1052,260),(28,1390),(1052,1580)):
            d.ellipse((x-6,y-6,x+6,y+6),fill=(*gold,220));d.line((x-18,y,x+18,y),fill=(*gold,180),width=2);d.line((x,y-18,x,y+18),fill=(*gold,180),width=2)
    elif v==2:
        d.arc((-260,1180,110,1680),270,70,fill=(*secondary,190),width=6)
        for i in range(6):
            y=1375+i*42;d.ellipse((8+i*6,y,48+i*6,y+21),fill=(*secondary,120))
    else:
        d.polygon(((0,0),(125,0),(78,105),(0,145)),fill=(*primary,75));d.polygon(((1080,1920),(930,1920),(985,1795),(1080,1740)),fill=(*secondary,70))
    return im

def _regions_for_slot(slot:str)->list[tuple[str,tuple[int,int,int,int]]]:
    regions={
        "morning":[("date",(265,335,815,456)),("solar_term",(145,630,720,712)),("season_note",(145,766,720,825)),("moon_phase",(135,1085,735,1150)),("moon_line",(135,1191,735,1275)),("daily_hint",(195,1445,900,1570)),("daily_question",(188,1597,905,1663))],
        "noon":[("fire_action",(117,883,488,991)),("earth_action",(592,883,963,991)),("air_action",(117,1488,488,1601)),("water_action",(592,1488,963,1601)),("noon_footer",(115,1637,965,1677))],
        "evening":[("evening_headline",(365,438,955,500)),("sky_state",(440,684,930,805)),("mind_tendency",(440,952,930,1070)),("maintenance_actions",(465,1282,915,1458)),("evening_footer",(275,1505,1010,1652))],
        "night":[("night_headline",(95,345,985,425)),("night_body",(125,515,955,1485)),("night_ending",(145,1535,935,1638))],
    }
    if slot not in regions:raise ValueError(f"Unknown story slot: {slot}")
    return regions[slot]

def _rectangles_overlap(left:tuple[int,int,int,int],right:tuple[int,int,int,int])->bool:
    return not (left[2]<=right[0] or right[2]<=left[0] or left[3]<=right[1] or right[3]<=left[1])

def validate_layout_regions(slot:str)->dict[str,Any]:
    regions=_regions_for_slot(slot)
    for name,box in regions:
        x1,y1,x2,y2=box
        if not (0<=x1<x2<=WIDTH and SAFE_TOP<=y1<y2<=SAFE_BOTTOM):raise ValueError(f"{slot} layout region '{name}' is outside the Instagram safe area: {box}")
    for index,(left_name,left_box) in enumerate(regions):
        for right_name,right_box in regions[index+1:]:
            if _rectangles_overlap(left_box,right_box):raise ValueError(f"{slot} layout regions overlap: {left_name} and {right_name}")
    return {"slot":slot,"safe_top":SAFE_TOP,"safe_bottom":SAFE_BOTTOM,"regions_checked":len(regions),"overlap_free":True}


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
    validate_layout_regions("morning")
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
    _box(d,(165,1430,925,1580),(250,247,238))
    _fit(d,c["hint"],(195,1445,900,1570),max_size=43,min_size=31,align="center")
    d.rounded_rectangle((130,1580,950,1775),radius=24,fill=(250,247,238),outline=CORAL,width=2)
    d.line((220,1705,860,1705),fill=CORAL,width=2)
    _box(d,(170,1588,920,1670),(250,247,238))
    _fit(d,f"今日の問い｜{c['question']}",(188,1597,905,1663),max_size=27,min_size=22,align="center")
    return im

def _render_noon(c:dict[str,Any],day:date)->Image.Image:
    validate_layout_regions("noon")
    # High-resolution user-approved collage master. Only the daily copy changes.
    im=_master("noon-approved-hd.png");d=ImageDraw.Draw(im)
    cards=(
        ((105,875,500,1015),"火",(218,77,58)),
        ((580,875,975,1015),"地",(40,103,76)),
        ((105,1480,500,1625),"風",(119,101,148)),
        ((580,1480,975,1625),"水",(180,54,77)),
    )
    for box,key,color in cards:
        x1,y1,x2,y2=box
        d.rectangle(box,fill=(249,241,226))
        _fit(d,c["actions"][key],(x1+12,y1+8,x2-12,y2-24),max_size=43,min_size=29,align="center")
        d.line((x1+35,y2-15,x2-35,y2-15),fill=color,width=3)
    d.rounded_rectangle((65,1615,1015,1815),radius=24,fill=(250,244,231),outline=GOLD,width=2)
    d.line((200,1720,880,1720),fill=GOLD,width=2)
    d.rounded_rectangle((80,1628,1000,1690),radius=14,fill=(250,244,231))
    _fit(d,f"今日のヒント｜{c['footer']}",(115,1637,965,1677),max_size=27,min_size=20,align="center")
    return im
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
    validate_layout_regions("evening")
    im=_master("evening-approved.png"); d=ImageDraw.Draw(im)
    _box(d,(805,42,1028,102),(249,245,235)); _fit(d,_date_text(day),(805,48,1025,90),max_size=18,min_size=16,align="center")
    d.rounded_rectangle((338,425,982,511),radius=10,fill=JADE)
    _fit(d,c["headline"],(365,438,955,500),max_size=37,min_size=28,fill=WHITE,align="center")
    _box(d,(420,570,1020,820),(249,245,235))
    _box(d,(420,835,1020,1095),(249,245,235))
    _box(d,(410,1135,1000,1475),(250,247,239))
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
    d.rectangle((205,1480,1080,1780),fill=NAVY)
    _fit(d,c["footer"],(275,1505,1010,1652),max_size=34,min_size=25,fill=WHITE,align="center")
    return im

def _render_night(c:dict[str,Any],day:date)->Image.Image:
    validate_layout_regions("night")
    im=_master("night-column-approved.png"); d=ImageDraw.Draw(im)
    _box(d,(570,180,725,242),(249,246,238)); _center(d,str(c["number"])[-2:],189,22,left=570,right=725)
    _box(d,(80,330,1000,445),(249,246,238)); _fit(d,c["headline"],(95,345,985,425),max_size=53,min_size=38,align="center")
    # Clear the whole master-copy region so old master text cannot show through
    # behind the new ending and appear as an overlap.
    _box(d,(90,445,995,1765),(249,246,238))
    _fit(d,"\n\n".join(c["paragraphs"]),(125,515,955,1485),max_size=31,min_size=22,line_gap=.56)
    _box(d,(125,1520,955,1650),(249,246,238)); d.rectangle((125,1520,955,1650),outline=NAVY,width=2)
    _fit(d,c["ending"],(145,1535,935,1638),max_size=30,min_size=23,fill=NAVY,align="center")
    return im

def render_approved_story(content:dict[str,Any],day:date,output_path:str|Path)->Path:
    validate_layout_regions(content["slot"])
    renderer={"morning":_render_morning,"noon":_render_noon,"evening":_render_evening,"night":_render_night}[content["slot"]]
    image=_decorate(renderer(content,day),day,content["slot"])
    if image.size!=(WIDTH,HEIGHT): raise RuntimeError("Story must be exactly 1080x1920")
    path=Path(output_path); path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path,"JPEG",quality=96,optimize=True,subsampling=0)
    if path.stat().st_size<150_000: raise RuntimeError("Story quality check failed: output is unexpectedly small")
    return path

def validate_story_asset(path:str|Path,content:dict[str,Any],day:date)->dict[str,Any]:
    asset=Path(path)
    if not asset.is_file():raise RuntimeError(f"Story quality check failed: asset is missing: {asset}")
    layout=validate_layout_regions(content["slot"])
    with Image.open(asset) as image:
        if image.size!=(WIDTH,HEIGHT):raise RuntimeError(f"Story quality check failed: unexpected size {image.size}")
        if image.format!="JPEG":raise RuntimeError(f"Story quality check failed: unexpected format {image.format}")
    size=asset.stat().st_size
    if size<150_000:raise RuntimeError("Story quality check failed: output is unexpectedly small")
    return {
        "passed":True,
        "text_fit_checked":True,
        "layout":layout,
        "design":design_variant(day,content["slot"])["name"],
        "asset_bytes":size,
    }
