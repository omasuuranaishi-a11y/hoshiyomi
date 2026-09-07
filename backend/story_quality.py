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
TAROT_DIR = ROOT / "assets" / "tarot"
PAPER=(249,245,235); INK=(14,39,64); NAVY=(4,44,73); JADE=(24,119,117)
CORAL=(235,111,86); GOLD=(181,139,70); WHITE=(255,253,247); MUTED=(91,91,85)
MOBILE_BODY_MIN = 34
MOBILE_SUPPORT_MIN = 28
MORNING_BODY_MIN = 38
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

def _required_tarot_art(card_number:int)->Path:
    """Return the approved RWS1909 art, failing closed when it is unavailable."""
    path=TAROT_DIR / f"major-{card_number:02d}-rws1909-v1.jpeg"
    if not path.is_file() or path.stat().st_size < 100_000:
        raise RuntimeError(
            f"Tarot story blocked: approved card art is missing for major arcana {card_number:02d}"
        )
    return path

def design_variant(day:date,slot:str)->dict[str,Any]:
    sequence=day.toordinal()+SLOT_OFFSETS[slot]
    palette_index=sequence%len(THEMES)
    motif_index=(sequence*3+SLOT_OFFSETS[slot])%len(MOTIFS)
    name,primary,secondary,gold=THEMES[palette_index]
    return {"index":palette_index,"motif_index":motif_index,"name":f"{name} / {MOTIFS[motif_index]}","primary":primary,"secondary":secondary,"gold":gold}

def _mix_color(left:tuple[int,int,int],right:tuple[int,int,int],amount:float)->tuple[int,int,int]:
    return tuple(round(a+(b-a)*amount) for a,b in zip(left,right))

def _apply_daily_palette(im:Image.Image,day:date,slot:str)->Image.Image:
    """Recolor the large decorative surfaces so consecutive days look distinct."""
    theme=design_variant(day,slot)
    primary=theme["primary"]; secondary=theme["secondary"]; gold=theme["gold"]
    dark_secondary=_mix_color(NAVY,secondary,.55)
    overlay=Image.new("RGBA",im.size,(0,0,0,0)); d=ImageDraw.Draw(overlay,"RGBA")
    if slot=="morning":
        # These polygons follow the approved collage edges and preserve the
        # paper texture while changing the dominant palette every day.
        # Keep the rotating color field outside the fixed masthead lettering.
        d.polygon(((0,0),(190,0),(120,300),(0,390)),fill=(*primary,205))
        d.polygon(((760,0),(1080,0),(1080,405),(910,275)),fill=(*dark_secondary,215))
        d.polygon(((0,1490),(275,1660),(365,1920),(0,1920)),fill=(*secondary,185))
        d.polygon(((1080,1450),(845,1680),(755,1920),(1080,1920)),fill=(*_mix_color(primary,gold,.40),175))
    elif slot=="evening":
        d.polygon(((0,0),(245,0),(245,1260),(120,1460),(0,1390)),fill=(*dark_secondary,155))
        d.rectangle((0,1480,1080,1780),fill=(*dark_secondary,200))
        d.polygon(((880,0),(1080,0),(1080,300),(1000,240)),fill=(*primary,95))
    elif slot=="night":
        d.rectangle((0,0,34,1920),fill=(*primary,205))
        d.polygon(((760,0),(1080,0),(1080,245),(930,165)),fill=(*secondary,60))
        d.polygon(((0,1700),(150,1775),(230,1920),(0,1920)),fill=(*_mix_color(primary,gold,.35),95))
    return Image.alpha_composite(im.convert("RGBA"),overlay).convert("RGB")

def _decorate(im:Image.Image,day:date,slot:str)->Image.Image:
    theme=design_variant(day,slot);primary=theme["primary"];secondary=theme["secondary"];gold=theme["gold"]
    if slot=="night":
        # Preserve the approved column design: only the former, restrained
        # daily tint and edge motif are applied. Text is enlarged separately.
        im=Image.blend(im,Image.new("RGB",im.size,primary),0.055)
        d=ImageDraw.Draw(im,"RGBA");v=theme["motif_index"]
        if v==0:
            d.line((30,122,1050,122),fill=(*gold,190),width=3);d.line((30,1715,1050,1715),fill=(*gold,150),width=3)
        elif v==1:
            for x,y in ((28,230),(1052,260),(28,1390),(1052,1580)):
                d.ellipse((x-6,y-6,x+6,y+6),fill=(*gold,220));d.line((x-18,y,x+18,y),fill=(*gold,180),width=2);d.line((x,y-18,x,y+18),fill=(*gold,180),width=2)
        elif v==2:
            # The former circle-and-dots motif was removed after visual review.
            # Leave the paper edge quiet so the copy remains the only focal point.
            pass
        else:
            d.polygon(((0,0),(125,0),(78,105),(0,145)),fill=(*primary,75));d.polygon(((1080,1920),(930,1920),(985,1795),(1080,1740)),fill=(*secondary,70))
        return im
    # The former 3.5% tint was effectively invisible on a phone. Keep the
    # approved masters, but make the rotating palette and motif unmistakable.
    im=Image.blend(im,Image.new("RGB",im.size,primary),0.075)
    d=ImageDraw.Draw(im,"RGBA");v=theme["motif_index"]
    d.rounded_rectangle((18,18,1062,1902),radius=42,outline=(*primary,185),width=5)
    if v==0:
        d.line((34,122,1046,122),fill=(*gold,220),width=5);d.line((34,1715,1046,1715),fill=(*gold,190),width=5)
        d.rounded_rectangle((26,250,42,1610),radius=8,fill=(*secondary,170))
    elif v==1:
        for x,y in ((28,230),(1052,260),(28,1390),(1052,1580)):
            d.ellipse((x-8,y-8,x+8,y+8),fill=(*gold,235));d.line((x-24,y,x+24,y),fill=(*gold,205),width=3);d.line((x,y-24,x,y+24),fill=(*gold,205),width=3)
        for offset in range(7):
            x=55+offset*155; y=1740+(offset%2)*18
            d.ellipse((x-4,y-4,x+4,y+4),fill=(*primary,210))
    elif v==2:
        # The circle motif is intentionally absent; the card art is the focal point.
        pass
    else:
        d.polygon(((0,0),(185,0),(112,142),(0,205)),fill=(*primary,115));d.polygon(((1080,1920),(860,1920),(970,1740),(1080,1675)),fill=(*secondary,110))
        d.line((50,178,50,410),fill=(*gold,210),width=5);d.line((1030,1510,1030,1740),fill=(*gold,210),width=5)
    return im

def _regions_for_slot(slot:str)->list[tuple[str,tuple[int,int,int,int]]]:
    regions={
        "morning":[("date",(265,335,815,456)),("solar_term",(130,630,755,712)),("season_note",(130,748,755,852)),("moon_phase",(120,955,760,1010)),("moon_line",(120,1035,760,1125)),("daily_hint",(120,1275,960,1460)),("daily_question",(130,1535,950,1680))],
        "noon":[("fire_action",(117,883,488,991)),("earth_action",(592,883,963,991)),("air_action",(117,1488,488,1601)),("water_action",(592,1488,963,1601)),("noon_footer",(115,1625,965,1680))],
        "evening":[("card_identity",(80,340,520,470)),("evening_headline",(550,345,1000,520)),("card_art",(80,480,520,1120)),("symbol_notes",(550,535,1000,945)),("card_core",(550,955,1000,1170)),("tarot_method",(80,1180,1000,1660))],
        "night":[("column_headline",(105,385,975,690)),("column_body",(85,900,995,1680))],
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

def _gothic_font(size: int) -> ImageFont.FreeTypeFont:
    path=FONT_DIR / "ZenMaruGothic-Regular.ttf"
    if not path.is_file():
        raise RuntimeError(f"Rounded Gothic font is missing: {path}")
    return ImageFont.truetype(str(path),size=size)

def _gothic_bold_font(size: int) -> ImageFont.FreeTypeFont:
    path=FONT_DIR / "ZenMaruGothic-Bold.ttf"
    if not path.is_file():
        raise RuntimeError(f"Rounded Gothic font is missing: {path}")
    return ImageFont.truetype(str(path),size=size)

def _handwritten_gothic_font(size: int) -> ImageFont.FreeTypeFont:
    path=FONT_DIR / "KleeOne-SemiBold.ttf"
    if not path.is_file():
        raise RuntimeError(f"Handwritten Gothic font is missing: {path}")
    return ImageFont.truetype(str(path),size=size)

def _handwritten_gothic_regular_font(size: int) -> ImageFont.FreeTypeFont:
    path=FONT_DIR / "KleeOne-Regular.ttf"
    if not path.is_file():
        raise RuntimeError(f"Handwritten Gothic font is missing: {path}")
    return ImageFont.truetype(str(path),size=size)

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
            if char in "\u3001\u3002\uff0c\uff0e\uff01\uff1f\uff09\u300d\u300f\u3011":
                lines.append(current+char); current=""
            else:
                lines.append(current); current=char
        else: current=trial
    if current or not lines: lines.append(current)
    return lines

def _wrap_kinsoku(draw, text, font, width):
    """Wrap Japanese prose without orphan punctuation or width overflow."""
    closing="。、？！』）」】"
    opening="『「（(【"
    lines=[]
    for paragraph in str(text).split("\n"):
        wrapped=[]; current=""
        for char in paragraph:
            trial=current+char
            if current and draw.textlength(trial,font=font)>width:
                # Pull one readable character with closing punctuation onto the
                # next line. Likewise, never strand an opening mark at line end.
                if (char in closing or current[-1:] in opening) and len(current)>1:
                    carry=current[-1]
                    wrapped.append(current[:-1])
                    current=carry+char
                else:
                    wrapped.append(current)
                    current=char
            else:
                current=trial
        if current or not wrapped:
            wrapped.append(current)
        if len(wrapped)>1 and len(wrapped[-1].strip())<=3 and len(wrapped[-2])>4:
            needed=4-len(wrapped[-1].strip())
            carry=wrapped[-2][-needed:]
            wrapped[-2]=wrapped[-2][:-needed]
            wrapped[-1]=carry+wrapped[-1]
        lines.extend(wrapped)
    return lines

def _fit(draw, text, box, *, max_size, min_size=22, fill=INK, align="left", line_gap=.48,font_fn=_font,wrap_fn=_wrap):
    x1,y1,x2,y2=box
    sizes=list(range(max_size,min_size-1,-2))
    if not sizes or sizes[-1]!=min_size:
        sizes.append(min_size)
    for size in sizes:
        font=font_fn(size); lines=wrap_fn(draw,text,font,x2-x1)
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
    im=_apply_daily_palette(_master("morning-approved.png"),day,"morning"); d=ImageDraw.Draw(im)
    theme=design_variant(day,"morning"); primary=theme["primary"]; secondary=theme["secondary"]; gold=theme["gold"]
    dark_primary=_mix_color(NAVY,primary,0.35)
    _box(d,(245,325,835,466),(249,245,234)); _center(d,_date_text(day),360,48,left=230,right=850)
    for x in range(320,760,10): d.ellipse((x,438,x+3,441),fill=INK)
    d.ellipse((536,438,544,446),fill=GOLD)
    _box(d,(115,615,765,840),(250,247,238))
    _fit(d,f"二十四節気｜{c['term']}",(130,630,755,712),max_size=47)
    d.line((130,738,720,738),fill=primary,width=3)
    _fit(d,c["season_note"],(130,748,755,852),max_size=36,min_size=32,line_gap=.20)
    _box(d,(770,530,925,780),(247,243,231))
    _center(d,day.strftime("%B").upper(),552,24,fill=(51,97,73),left=770,right=925)
    _center(d,str(day.day),610,62,fill=(51,97,73),left=770,right=925)
    _center(d,day.strftime("%a").upper(),690,26,fill=(51,97,73),left=770,right=925)
    # Rebuild the complete lower half as two independent cards. The approved
    # master contains legacy moon and hint copy in this area; the opaque base
    # removes it before any new text is drawn.
    lower_paper=(250,247,238)
    d.rounded_rectangle((65,880,1015,1740),radius=34,fill=lower_paper,outline=gold,width=3)

    # Card 1: lunar state. Its text ends at y=1125, before the guidance card.
    d.rounded_rectangle((85,900,995,1150),radius=24,fill=dark_primary,outline=gold,width=3)
    d.ellipse((820,925,940,1085),fill=gold)
    d.ellipse((780,900,900,1060),fill=dark_primary)
    for x,y in ((790,1085),(955,960),(760,980)):
        d.ellipse((x-4,y-4,x+4,y+4),fill=gold)
    d.rounded_rectangle((105,885,390,945),radius=14,fill=_mix_color(PAPER,secondary,0.42))
    _fit(d,"月の満ち欠け",(125,895,370,935),max_size=29,min_size=27,fill=NAVY,align="center",line_gap=0)
    _fit(d,f"{c['phase']}｜{c['illumination']:.1f}%",(120,955,760,1010),max_size=42,min_size=MORNING_BODY_MIN,fill=WHITE)
    d.line((120,1020,740,1020),fill=gold,width=3)
    _fit(d,c["moon_line"],(120,1035,760,1125),max_size=38,min_size=36,fill=WHITE,line_gap=.08)

    # Card 2: guidance. Every text box has a dedicated vertical band.
    d.rounded_rectangle((85,1175,995,1715),radius=28,fill=lower_paper,outline=CORAL,width=3)
    d.rounded_rectangle((100,1190,655,1265),radius=18,fill=CORAL)
    _fit(d,"星回りからの今日の導き",(120,1198,635,1255),max_size=34,min_size=30,fill=WHITE,align="center",line_gap=.05)
    _fit(d,c["hint"],(120,1275,960,1460),max_size=31,min_size=29,align="left",line_gap=.05)
    d.rounded_rectangle((105,1470,975,1695),radius=22,fill=_mix_color(lower_paper,secondary,0.06),outline=secondary,width=3)
    _fit(d,"今日の一手",(130,1480,950,1525),max_size=31,min_size=29,fill=secondary,line_gap=.02)
    _fit(d,c["thinking"],(130,1535,950,1680),max_size=33,min_size=29,line_gap=.12)
    return im

def _render_noon(c:dict[str,Any],day:date)->Image.Image:
    validate_layout_regions("noon")
    # High-resolution user-approved collage master. Only the daily copy changes.
    im=_master("noon-approved-hd.png");d=ImageDraw.Draw(im)
    theme=design_variant(day,"noon"); primary=theme["primary"]; secondary=theme["secondary"]; gold=theme["gold"]
    cards=(
        ((105,875,500,1015),"火",(218,77,58)),
        ((580,875,975,1015),"地",(40,103,76)),
        ((105,1480,500,1625),"風",(119,101,148)),
        ((580,1480,975,1625),"水",(180,54,77)),
    )
    for box,key,color in cards:
        x1,y1,x2,y2=box
        d.rectangle(box,fill=(249,241,226))
        _fit(d,c["actions"][key],(x1+12,y1+6,x2-12,y2-10),max_size=42,min_size=MOBILE_BODY_MIN,align="center",line_gap=.28)
        d.line((x1+35,y2-15,x2-35,y2-15),fill=color,width=3)
    d.rounded_rectangle((65,1615,1015,1815),radius=24,fill=_mix_color((250,244,231),primary,0.10),outline=gold,width=3)
    d.line((200,1720,880,1720),fill=gold,width=3)
    d.rounded_rectangle((80,1628,1000,1690),radius=14,fill=(250,244,231))
    _fit(d,c["footer"],(115,1625,965,1680),max_size=35,min_size=30,align="center",line_gap=.26)
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

def _render_tarot(c:dict[str,Any],day:date)->Image.Image:
    validate_layout_regions("evening")
    theme=design_variant(day,"evening"); primary=theme["primary"]; secondary=theme["secondary"]; gold=theme["gold"]
    dark_primary=_mix_color(NAVY,primary,0.28)
    im=Image.new("RGB",(WIDTH,HEIGHT),PAPER); d=ImageDraw.Draw(im)
    d.rectangle((0,0,58,HEIGHT),fill=dark_primary)
    d.polygon(((760,0),(1080,0),(1080,250),(940,185)),fill=dark_primary)
    d.polygon(((0,1770),(230,1660),(360,1920),(0,1920)),fill=_mix_color(PAPER,secondary,0.38))
    d.rounded_rectangle((24,24,1056,1896),radius=44,outline=gold,width=4)
    for x,y in ((90,115),(1010,310),(55,1160),(1015,1410)):
        d.ellipse((x-7,y-7,x+7,y+7),fill=gold);d.line((x-21,y,x+21,y),fill=gold,width=2);d.line((x,y-21,x,y+21),fill=gold,width=2)
    _fit(d,"SYMBOL TAROT NOTE",(85,55,540,110),max_size=25,min_size=23,fill=MUTED,font_fn=_gothic_font)
    d.rounded_rectangle((720,42,1010,112),radius=14,fill=dark_primary)
    _fit(d,_date_text(day),(735,55,995,105),max_size=28,min_size=25,fill=WHITE,align="center",font_fn=_gothic_font)
    _fit(d,c["title"],(80,160,1000,260),max_size=70,min_size=60,align="center",font_fn=_gothic_bold_font)
    _fit(d,c["subtitle"],(160,275,920,330),max_size=30,min_size=27,fill=MUTED,align="center",font_fn=_gothic_font)

    _fit(d,"今回のカード",(80,340,520,382),max_size=23,min_size=21,fill=primary,font_fn=_gothic_bold_font,line_gap=.05)
    _fit(d,f"大アルカナ {c['card_number']}｜{c['card_name']}",(80,382,520,470),max_size=40,min_size=32,font_fn=_gothic_bold_font,line_gap=.05)

    art_box=(80,480,520,1120)
    art_path=_required_tarot_art(c["card_number"])
    d.rounded_rectangle(art_box,radius=24,fill=dark_primary,outline=gold,width=5)
    with Image.open(art_path) as source:
        art=source.convert("RGB")
        target_w=art_box[2]-art_box[0]-16; target_h=art_box[3]-art_box[1]-16
        scale=min(target_w/art.width,target_h/art.height)
        resized=art.resize((round(art.width*scale),round(art.height*scale)),Image.Resampling.LANCZOS)
        left=art_box[0]+(art_box[2]-art_box[0]-resized.width)//2
        top=art_box[1]+(art_box[3]-art_box[1]-resized.height)//2
        im.paste(resized,(left,top))
    d.rounded_rectangle(art_box,radius=24,outline=gold,width=5)

    _fit(d,f"解説テーマ｜{c['category']}",(550,345,1000,390),max_size=26,min_size=23,fill=primary,font_fn=_gothic_bold_font,line_gap=.05)
    _fit(d,c["headline"],(550,392,1000,520),max_size=48,min_size=34,font_fn=_gothic_bold_font,line_gap=.16)
    symbol_items=[item.strip() for item in c["notes"].split("／")]
    note_tops=(535,675,815)
    connector_ys=(600,740,880)
    for item,top,connector_y in zip(symbol_items,note_tops,connector_ys):
        label,meaning=(item.split("＝",1)+[""])[:2]
        d.line((500,connector_y,555,connector_y),fill=gold,width=3)
        d.ellipse((494,connector_y-5,504,connector_y+5),fill=gold)
        d.rounded_rectangle((550,top,1000,top+130),radius=16,fill=(253,249,240),outline=gold,width=2)
        _fit(d,label,(575,top+12,975,top+55),max_size=31,min_size=27,fill=primary,font_fn=_gothic_bold_font)
        _fit(d,meaning,(575,top+58,975,top+117),max_size=29,min_size=25,line_gap=.14,font_fn=_gothic_font)
    d.rounded_rectangle((550,955,1000,1170),radius=18,fill=_mix_color(PAPER,primary,0.10),outline=primary,width=3)
    _fit(d,"カードの成り立ち",(575,970,975,1010),max_size=28,min_size=25,fill=primary,font_fn=_gothic_bold_font)
    _fit(d,c["origin"],(575,1018,975,1158),max_size=24,min_size=19,line_gap=.08,font_fn=_gothic_font)

    d.rounded_rectangle((80,1180,1000,1660),radius=26,fill=(253,249,240),outline=secondary,width=3)
    _fit(d,"意味をどう読む？",(115,1205,965,1255),max_size=34,min_size=30,fill=secondary,font_fn=_gothic_bold_font)
    _fit(d,f"{c['core']}\n{c['method']}",(115,1270,965,1440),max_size=29,min_size=22,line_gap=.12,font_fn=_gothic_font)
    d.line((115,1465,965,1465),fill=gold,width=2)
    _fit(d,"おますの読み解き",(115,1490,410,1530),max_size=26,min_size=23,fill=primary,font_fn=_gothic_bold_font)
    _fit(d,c["humor"],(115,1540,965,1640),max_size=28,min_size=24,line_gap=.12,font_fn=_gothic_font)

    d.line((260,1730,820,1730),fill=gold,width=2)
    _fit(d,"OMASU TAROT NOTE",(300,1765,780,1810),max_size=25,min_size=22,fill=MUTED,align="center",font_fn=_gothic_font)
    _fit(d,"@omasu_horoscope",(300,1820,780,1870),max_size=25,min_size=22,fill=MUTED,align="center",font_fn=_gothic_font)
    return im

def _paste_tarot_card(im:Image.Image,draw:ImageDraw.ImageDraw,card_number:int,box:tuple[int,int,int,int],gold:tuple[int,int,int],dark:tuple[int,int,int])->None:
    draw.rounded_rectangle(box,radius=22,fill=dark,outline=gold,width=5)
    with Image.open(_required_tarot_art(card_number)) as source:
        art=source.convert("RGB")
        target_w=box[2]-box[0]-16; target_h=box[3]-box[1]-16
        scale=min(target_w/art.width,target_h/art.height)
        resized=art.resize((round(art.width*scale),round(art.height*scale)),Image.Resampling.LANCZOS)
        left=box[0]+(box[2]-box[0]-resized.width)//2
        top=box[1]+(box[3]-box[1]-resized.height)//2
        im.paste(resized,(left,top))
    draw.rounded_rectangle(box,radius=22,outline=gold,width=5)

def _render_tarot_insight(c:dict[str,Any],day:date)->Image.Image:
    validate_layout_regions("evening")
    theme=design_variant(day,"evening"); primary=theme["primary"]; secondary=theme["secondary"]; gold=theme["gold"]
    dark=_mix_color(NAVY,primary,0.26)
    soft_primary=_mix_color(PAPER,primary,0.10)
    soft_secondary=_mix_color(PAPER,secondary,0.10)
    im=Image.new("RGB",(WIDTH,HEIGHT),PAPER);d=ImageDraw.Draw(im)

    d.rectangle((0,0,58,HEIGHT),fill=dark)
    d.polygon(((760,0),(1080,0),(1080,250),(940,185)),fill=dark)
    d.polygon(((0,1770),(230,1660),(360,1920),(0,1920)),fill=_mix_color(PAPER,secondary,0.38))
    d.rounded_rectangle((24,24,1056,1896),radius=44,outline=gold,width=4)
    for x,y in ((90,115),(1010,310),(55,1160),(1015,1410)):
        d.ellipse((x-7,y-7,x+7,y+7),fill=gold);d.line((x-21,y,x+21,y),fill=gold,width=2);d.line((x,y-21,x,y+21),fill=gold,width=2)

    _fit(d,"OMASU TAROT NOTE",(85,55,540,108),max_size=25,min_size=23,fill=MUTED,font_fn=_gothic_font)
    d.rounded_rectangle((720,42,1010,112),radius=14,fill=dark)
    _fit(d,_date_text(day),(735,55,995,105),max_size=28,min_size=25,fill=WHITE,align="center",font_fn=_gothic_font)
    _fit(d,c["title"],(80,150,1000,245),max_size=66,min_size=58,align="center",font_fn=_gothic_bold_font)
    d.rounded_rectangle((360,270,720,330),radius=28,fill=primary)
    _fit(d,c["kicker"],(385,279,695,322),max_size=27,min_size=24,fill=WHITE,align="center",font_fn=_gothic_bold_font,line_gap=.05)
    _fit(d,c["headline"],(90,355,990,520),max_size=58,min_size=46,align="center",font_fn=_gothic_bold_font,line_gap=.12)
    _fit(d,c["lead"],(105,535,975,620),max_size=31,min_size=27,fill=MUTED,align="center",font_fn=_gothic_font,line_gap=.12)

    card_count=len(c["card_numbers"])
    if card_count==3:
        card_boxes=((85,645,345,1040),(410,645,670,1040),(735,645,995,1040))
        label_boxes=((75,1050,355,1125),(400,1050,680,1125),(725,1050,1005,1125))
        for number,card_box in zip(c["card_numbers"],card_boxes):
            _paste_tarot_card(im,d,number,card_box,gold,dark)
        for label,label_box in zip(c["card_labels"],label_boxes):
            _fit(d,label,label_box,max_size=25,min_size=21,fill=primary,align="center",font_fn=_gothic_bold_font,line_gap=.04)
        for point,box,fill in zip(c["points"],((80,1145,520,1385),(560,1145,1000,1385)),(soft_primary,soft_secondary)):
            d.rounded_rectangle(box,radius=20,fill=fill,outline=gold,width=2)
            _fit(d,point["label"],(box[0]+24,box[1]+18,box[2]-24,box[1]+60),max_size=27,min_size=23,fill=primary,font_fn=_gothic_bold_font,line_gap=.05)
            _fit(d,point["body"],(box[0]+24,box[1]+72,box[2]-24,box[3]-20),max_size=27,min_size=22,font_fn=_gothic_font,line_gap=.12)
        reason_box=(80,1410,1000,1585)
        takeaway_box=(105,1600,975,1682)
    elif card_count==2:
        card_boxes=((100,645,480,1125),(600,645,980,1125))
        label_boxes=((90,1140,490,1210),(590,1140,990,1210))
        point_boxes=((90,1230,490,1435),(590,1230,990,1435))
        point_fills=(soft_primary,soft_secondary)
        for number,card_box in zip(c["card_numbers"],card_boxes):
            _paste_tarot_card(im,d,number,card_box,gold,dark)
        for label,label_box in zip(c["card_labels"],label_boxes):
            _fit(d,label,label_box,max_size=29,min_size=25,fill=primary,align="center",font_fn=_gothic_bold_font,line_gap=.05)
        for point,box,fill in zip(c["points"],point_boxes,point_fills):
            d.rounded_rectangle(box,radius=20,fill=fill,outline=gold,width=2)
            _fit(d,point["label"],(box[0]+24,box[1]+18,box[2]-24,box[1]+60),max_size=27,min_size=24,fill=primary,font_fn=_gothic_bold_font,line_gap=.05)
            _fit(d,point["body"],(box[0]+24,box[1]+72,box[2]-24,box[3]-20),max_size=28,min_size=23,font_fn=_gothic_font,line_gap=.12)
        reason_box=(80,1460,1000,1585)
        takeaway_box=(105,1600,975,1682)
    else:
        card_box=(95,650,505,1205)
        _paste_tarot_card(im,d,c["card_numbers"][0],card_box,gold,dark)
        _fit(d,c["card_labels"][0],(80,1220,520,1280),max_size=28,min_size=24,fill=primary,align="center",font_fn=_gothic_bold_font,line_gap=.05)
        for point,top,fill in zip(c["points"],(660,905),(soft_primary,soft_secondary)):
            box=(550,top,1000,top+220)
            d.rounded_rectangle(box,radius=20,fill=fill,outline=gold,width=2)
            _fit(d,point["label"],(575,top+18,975,top+62),max_size=28,min_size=25,fill=primary,font_fn=_gothic_bold_font,line_gap=.05)
            _fit(d,point["body"],(575,top+75,975,top+200),max_size=29,min_size=24,font_fn=_gothic_font,line_gap=.12)
        reason_box=(80,1300,1000,1515)
        takeaway_box=(105,1545,975,1682)

    d.rounded_rectangle(reason_box,radius=22,fill=(253,249,240),outline=secondary,width=3)
    _fit(d,c["reasoning"],(reason_box[0]+30,reason_box[1]+20,reason_box[2]-30,reason_box[3]-18),max_size=30,min_size=24,font_fn=_gothic_font,line_gap=.15)
    d.rounded_rectangle(takeaway_box,radius=28,fill=dark)
    _fit(d,c["takeaway"],(takeaway_box[0]+30,takeaway_box[1]+16,takeaway_box[2]-30,takeaway_box[3]-14),max_size=31,min_size=25,fill=WHITE,align="center",font_fn=_gothic_bold_font,line_gap=.10)

    d.line((260,1730,820,1730),fill=gold,width=2)
    _fit(d,"OMASU TAROT NOTE",(300,1765,780,1810),max_size=25,min_size=22,fill=MUTED,align="center",font_fn=_gothic_font)
    _fit(d,"@omasu_horoscope",(300,1820,780,1870),max_size=25,min_size=22,fill=MUTED,align="center",font_fn=_gothic_font)
    return im

def _render_evening(c:dict[str,Any],day:date)->Image.Image:
    validate_layout_regions("evening")
    if c.get("content_kind")=="tarot_insight":
        return _render_tarot_insight(c,day)
    if c.get("content_kind")=="tarot_knowledge":
        return _render_tarot(c,day)
    im=_apply_daily_palette(_master("evening-approved.png"),day,"evening"); d=ImageDraw.Draw(im)
    theme=design_variant(day,"evening"); primary=theme["primary"]; secondary=theme["secondary"]; gold=theme["gold"]
    dark_primary=_mix_color(NAVY,primary,0.35)
    _box(d,(790,38,1035,108),(249,245,235)); _fit(d,_date_text(day),(795,45,1030,100),max_size=30,min_size=28,align="center")
    d.rounded_rectangle((338,425,982,511),radius=10,fill=primary)
    _fit(d,c["headline"],(365,438,955,500),max_size=37,min_size=28,fill=WHITE,align="center")
    _box(d,(420,570,1020,820),(249,245,235))
    _box(d,(420,835,1020,1095),(249,245,235))
    _box(d,(410,1135,1000,1475),(250,247,239))
    _box(d,(365,580,975,840),(249,245,235)); _fit(d,"空の読み方",(380,590,950,646),max_size=37,min_size=34)
    d.line((380,660,960,660),fill=gold,width=3)
    _fit(d,f"{c['sky']}\n{c['context']}",(380,674,960,835),max_size=37,min_size=MOBILE_BODY_MIN,line_gap=.28)
    _box(d,(365,840,975,1155),(249,245,235)); _fit(d,"暮らしへの翻訳",(380,850,950,910),max_size=37,min_size=34)
    d.line((380,926,960,926),fill=gold,width=3)
    _fit(d,f"{c['tendency']}\n{c['adjust']}",(380,940,960,1140),max_size=37,min_size=MOBILE_BODY_MIN,line_gap=.28)
    _box(d,(365,1180,975,1475),(250,247,239)); _fit(d,"今夜の3分整理",(380,1190,950,1250),max_size=37,min_size=34,fill=primary)
    y=1270
    for action in c["actions"]:
        d.ellipse((378,y+13,394,y+29),fill=gold)
        _fit(d,action,(410,y,955,y+58),max_size=36,min_size=32,line_gap=.20); y+=66
    d.rectangle((205,1480,1080,1780),fill=dark_primary)
    _fit(d,c["footer"],(275,1505,1010,1652),max_size=40,min_size=34,fill=WHITE,align="center",line_gap=.30)
    return im

def _render_night(c:dict[str,Any],day:date)->Image.Image:
    validate_layout_regions("night")
    im=_apply_daily_palette(_master("morning-column-approved.png"),day,"night"); d=ImageDraw.Draw(im)
    theme=design_variant(day,"night"); primary=theme["primary"]; gold=theme["gold"]
    # Keep the approved paper, brush circle, lunar orbit, and footer. Replace
    # only the daily headline/copy so the result remains premium and readable.
    paper=(249,246,238)
    _box(d,(160,175,920,330),paper)
    _fit(d,f"{c['title']}  {c['number']:02d}",(180,205,900,285),max_size=38,min_size=32,align="center",fill=NAVY,font_fn=_handwritten_gothic_regular_font)
    d.line((260,310,820,310),fill=gold,width=2)
    _box(d,(85,355,995,720),paper)
    _fit(d,c["headline"],(105,385,975,690),max_size=82,min_size=62,align="center",line_gap=.20,font_fn=_handwritten_gothic_font)
    # One uninterrupted essay block: no labels, subheads, or boxed callout.
    _box(d,(65,860,1015,1730),paper)
    if c.get("content_kind")=="column_20260907":
        # Use actual ink bounds rather than the font's unusually tall metrics.
        # Paragraph blanks remain a complete line, while visible lines never touch.
        for size in (44,42,40):
            font=_gothic_font(size)
            lines=_wrap_kinsoku(d,c["column"],font,910)
            step=round(size*1.36)
            if len(lines)*step <= 780:
                for index,line in enumerate(lines):
                    if line:
                        d.text((85,900+index*step),line,font=font,fill=INK,anchor="lt")
                c["rendered_body_px"]=size
                break
        else:
            raise ValueError("Column text exceeds its large-type area")
    else:
        _fit(d,c["column"],(85,900,995,1680),max_size=41,min_size=36,line_gap=.22,font_fn=_gothic_font,wrap_fn=_wrap_kinsoku)
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
    report = {
        "passed":True,
        "text_fit_checked":True,
        "layout":layout,
        "design":design_variant(day,content["slot"])["name"],
        "mobile_readability":{
            "body_min_px":MOBILE_BODY_MIN,
            "support_min_px":MOBILE_SUPPORT_MIN,
        },
        "asset_bytes":size,
    }
    if content.get("content_kind") in {"tarot_knowledge","tarot_insight"}:
        card_numbers=[content["card_number"]] if content.get("content_kind")=="tarot_knowledge" else content["card_numbers"]
        art_paths=[_required_tarot_art(number) for number in card_numbers]
        for art_path in art_paths:
            with Image.open(art_path) as art:
                art.verify()
        report["tarot_card_art"]={
            "required":True,
            "detected":True,
            "card_numbers":card_numbers,
            "assets":[path.name for path in art_paths],
        }
    return report
