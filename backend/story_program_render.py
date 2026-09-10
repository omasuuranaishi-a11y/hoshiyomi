"""Large-type native rendering of the approved encyclopedia and twelve-sign sheet."""
from pathlib import Path
import math
import re
from PIL import Image, ImageDraw, ImageFont
from .story_quality import FONT_DIR, TAROT_DIR, _wrap_kinsoku

INK="#24464b"; PAPER="#f6f2e8"; GOLD="#b89b71"
PALETTES={"iching":("#49736b","#e4ebe0"),"house4":("#537767","#e5e9dd"),"numerology":("#a87559","#f0dfd3"),"lunation":("#496683","#e4e8ed"),"runes":("#7c7288","#e8e3ec"),"elements":("#907a55","#eee7d9"),"tarot":("#486e70","#e3e9e5")}


def _wrap_horoscope_sentences(draw,text,font,width):
    """Keep each short horoscope sentence together, not the next word's head."""
    sentences=[part.strip() for part in re.split(r"(?<=[。！？])|\n",str(text)) if part.strip()]
    # All current sentences fit one line at 38px. Retain ordinary width/kinsoku
    # checks for future longer copy instead of drawing outside the card.
    return [line for sentence in sentences for line in _wrap_kinsoku(draw,sentence,font,width)]


class Canvas:
    def __init__(self,accent,wash):
        self.im=Image.new("RGB",(1080,1920),PAPER)
        self.d=ImageDraw.Draw(self.im)
        self.accent,self.wash=accent,wash
        self.regions=[]
        self.d.rounded_rectangle((48,25,1055,1895),radius=24,outline=GOLD,width=2)
        self.d.rectangle((0,0,28,1920),fill=accent)
        self.d.line((28,0,28,1920),fill=GOLD,width=4)
        self.d.polygon(((930,0),(1080,0),(1080,114)),fill=wash)

    def text(self,text,box,size=46,bold=False,fill=INK,center=False,leading=1.40,wrap_fn=_wrap_kinsoku):
        x,y,r,b=box
        font=ImageFont.truetype(str(FONT_DIR/('ZenMaruGothic-Bold.ttf' if bold else 'ZenMaruGothic-Regular.ttf')),size=size)
        lines=wrap_fn(self.d,text,font,r-x)
        step=round(size*leading)
        if y+(len(lines)-1)*step+size>b:
            raise ValueError(f"Large-type text exceeds box: {text[:35]}")
        boxes=[]
        for i,line in enumerate(lines):
            if not line: continue
            xx=(x+r-self.d.textlength(line,font=font))/2 if center else x
            yy=y+i*step
            bbox=self.d.textbbox((xx,yy),line,font=font,anchor="lt")
            if bbox[2]>r+1 or bbox[3]>b+1:
                raise ValueError(f"Text ink outside box: {line}")
            self.d.text((xx,yy),line,font=font,fill=fill,anchor="lt")
            boxes.append(bbox)
        self.regions.append({"text":text,"size":size,"boxes":boxes})
        return lines

    def header(self,day,title,category=None):
        self.text(day.strftime("%Y.%m.%d"),(85,141,440,184),34,fill="#64766e")
        self.text("17:00" if category else "08:00",(815,141,1000,184),34,fill="#64766e",center=True)
        self.d.line((85,198,1004,198),fill=GOLD,width=2)
        self.text(title,(85,234,1004,307),50,True,center=True)
        if category:self.text(category,(80,320,1004,376),38,True,fill=self.accent,center=True)

    def footer(self):
        self.d.line((89,1796,1004,1796),fill=GOLD,width=1)
        self.text("@omasu_horoscope",(89,1821,1004,1870),34,fill="#65746e",center=True)

    def save(self,path,content):
        boxes=[(r["text"],b) for r in self.regions for b in r["boxes"]]
        for i,(a,x) in enumerate(boxes):
            for b,y in boxes[i+1:]:
                if x[0]<y[2]-.5 and x[2]>y[0]+.5 and x[1]<y[3]-.5 and x[3]>y[1]+.5:
                    raise ValueError(f"Text overlap: {a[:15]} / {b[:15]}")
        # Subtle deterministic grain keeps the paper feel without changing geometry.
        noise=Image.effect_noise(self.im.size,7).convert("RGB")
        self.im=Image.blend(self.im,noise,.025)
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        self.im.save(path,"JPEG",quality=96,subsampling=0)
        content["render_check"]={"overlap_free":True,"text_regions":len(self.regions),"minimum_px":min(r["size"] for r in self.regions),"body_px":46 if content["slot"]=="evening" else 38}
        if content["slot"]=="noon":
            content["render_check"]["linebreak_policy"]="one_sentence_per_line_v1"
        return path


def _moon(c,cx,cy,angle):
    r=78;box=(cx-r,cy-r,cx+r,cy+r)
    c.d.ellipse(box,fill="#486177")
    if angle==180:c.d.ellipse(box,fill="#ede0b9")
    elif angle==90:c.d.pieslice(box,-90,90,fill="#ede0b9")
    elif angle==270:c.d.pieslice(box,90,270,fill="#ede0b9")
    c.d.ellipse(box,outline="#d4c79f",width=2)


def _graphic(c,g):
    d=c.d;t=g["type"]
    if t=="hexagram":
        d.rounded_rectangle((89,614,1004,1040),18,fill="#eeeede",outline="#b5bcaa",width=2)
        for i,v in enumerate(g["lines"]):
            y=660+i*51+(30 if i>=3 else 0)
            if v:d.rectangle((150,y,457,y+21),fill=INK)
            else:
                d.rectangle((150,y,283,y+21),fill=c.accent);d.rectangle((324,y,457,y+21),fill=c.accent)
        c.text("上の三本",(650,668,975,720),38)
        c.text(g["upper"],(560,720,645,805),68,True,fill=c.accent)
        c.text("受けとめる",(650,743,985,801),40)
        d.line((560,842,982,842),fill=GOLD,width=1)
        c.text("下の三本",(650,872,975,925),38)
        c.text(g["lower"],(560,928,645,1012),68,True,fill=c.accent)
        c.text("はたらきかける" if g['lower']=='天' else "しなやかに応じる",(650,945,990,1005),38)
    elif t=="moon":
        for i in range(2):
            x=89+i*470
            d.rounded_rectangle((x,614,x+445,1040),20,fill=("#284958","#3f5068")[i])
            c.text(f"{g['labels'][i]} {g['angles'][i]}°",(x+20,656,x+425,720),44,True,fill="#f4eedf",center=True)
            _moon(c,x+222,825,g['angles'][i])
            c.text(g['notes'][i],(x+15,946,x+430,1006),40,fill="#f4eedf",center=True)
    elif t=="houses":
        cx,cy,r=299,822,193
        for i in range(12):
            house=i+1;a=180-i*30
            color=c.accent if house==g['house'] else '#c6b797' if house==g['opposite'] else '#eee9dd'
            d.pieslice((cx-r,cy-r,cx+r,cy+r),a-30,a,fill=color,outline=GOLD,width=1)
        d.ellipse((cx-104,cy-104,cx+104,cy+104),fill=PAPER,outline=GOLD,width=1)
        for i in range(12):
            angle=math.radians(165-i*30);x=cx+154*math.cos(angle);y=cy+154*math.sin(angle)
            c.text(str(i+1),(x-25,y-20,x+25,y+28),36,True,fill=PAPER if i+1==g['house'] else INK,center=True)
        c.text(str(g['house']),(cx-60,750,cx+60,840),72,True,fill=c.accent,center=True)
        c.text("模式図",(cx-90,862,cx+90,912),34,center=True)
        for i,(name,label) in enumerate(zip((f"第{g['house']}ハウス",f"向かいの第{g['opposite']}"),g['labels'])):
            y=640+i*201
            d.rounded_rectangle((550,y,1004,y+171),15,fill=c.wash if i==0 else '#ede6d5')
            c.text(name,(575,y+25,985,y+85),44,True)
            c.text(label,(575,y+99,985,y+158),40)
    elif t=="number":
        d.rounded_rectangle((89,614,1004,1040),20,fill="#faf7ef",outline=GOLD,width=2)
        c.text("計算例 "+g['example'],(118,642,960,694),36)
        for i,line in enumerate(g['parts']):c.text(line,(120,728+i*65,738,788+i*65),36)
        c.text(str(g['number']),(778,746,961,951),160,True,fill=c.accent,center=True)
        d.rounded_rectangle((116,944,976,1020),10,fill=c.wash)
        c.text(g['sum'],(130,962,958,1012),40,True,center=True)
    elif t=="runes":
        rune_lines=[[(0,160),(0,10),(80,-10)],[(0,160),(0,10),(85,48),(85,160)],[(0,160),(0,10),(85,45),(0,83),(87,160)]]
        for i,lines in enumerate(rune_lines):
            x=141+i*293
            d.rounded_rectangle((x,633,x+213,921),58,fill=("#c9bda6","#aec0b4","#b6adbf")[i])
            d.line([(x+64+a,688+b) for a,b in lines],fill=INK,width=9,joint="curve")
            if i==0:d.line((x+64,772,x+144,742),fill=INK,width=9)
            c.text(("F","U","R")[i],(x,945,x+213,1000),44,True,center=True)
        c.text("文字の形と音の例",(90,1025,1004,1070),34,center=True)
    elif t=="elements":
        names=("火","地","風","水");colors=("#f1dfd2","#e3e9dc","#e3ebeb","#e6e6ef")
        for i,name in enumerate(names):
            x=89+(i%2)*470;y=614+(i//2)*219
            d.rounded_rectangle((x,y,x+445,y+203),16,fill=colors[i],outline=GOLD,width=1)
            c.text(name,(x+20,y+32,x+90,y+100),48,True,fill=c.accent)
            c.text(g['labels'][i],(x+100,y+30,x+429,y+88),38,True)
            c.text(g['notes'][i],(x+100,y+112,x+429,y+175),36)
    elif t=="tarot":
        art=TAROT_DIR/f"major-{g['number']:02d}-rws1909-v1.jpeg"
        if not art.is_file():raise RuntimeError("Approved tarot art missing")
        img=Image.open(art).convert("RGB");img.thumbnail((255,419),Image.Resampling.LANCZOS)
        c.im.paste(img,(132+(255-img.width)//2,614))
        c.text(g['name'],(440,639,1003,756),42,True)
        for i,label in enumerate(g['labels']):
            d.rounded_rectangle((440,768+i*86,1004,837+i*86),12,fill=c.wash)
            c.text(label,(459,784+i*86,988,837+i*86),38)


def render_program(content,day,path):
    if content['slot']=='evening':
        from .story_dictionary_celestial import START,render_dictionary
        if day>=START:return render_dictionary(content,day,path)
    if content["slot"]=="noon":
        from .story_horoscope_celestial import START,render_celestial_horoscope
        if day>=START:
            return render_celestial_horoscope(content,day,path)
    if content["slot"]=="noon":
        c=Canvas("#496e74","#e4ece7");c.header(day,content['title'])
        c.text("太陽星座から読む、今日のヒント",(85,326,1004,375),34,center=True)
        colors=("#f2e1d5","#e6ebdd","#e5edef","#e9e5ee")
        for i,item in enumerate(content['items']):
            x=89+(i%2)*470;y=404+(i//2)*209
            c.d.rounded_rectangle((x,y,x+445,y+193),15,fill=colors[item['element']])
            c.text(item['sign'],(x+20,y+17,x+425,y+70),42,True)
            item['rendered_lines']=c.text(item['text'],(x+20,y+80,x+425,y+182),38,leading=1.32,wrap_fn=_wrap_horoscope_sentences)
        c.text(f"月は{content['moon_sign']}｜一般向けの星よみ",(85,1709,1004,1760),34,center=True)
    else:
        accent,wash=PALETTES[content['id']];c=Canvas(accent,wash)
        c.header(day,content['title'],content['category'])
        c.text(content['headline'],(80,411,1004,598),72,True,center=True,leading=1.35)
        _graphic(c,content['graphic'])
        c.text(content['heading'],(89,1094,1004,1153),42,True,fill=accent)
        c.text(content['body'],(89,1178,1004,1435),46,leading=1.4)
        c.d.rounded_rectangle((89,1455,1004,1760),18,fill=wash)
        c.d.line((89,1455,89,1760),fill=accent,width=5)
        c.text(content['note_title'],(117,1480,975,1534),38,True,fill=accent)
        c.text(content['note'],(117,1551,975,1746),44,leading=1.4)
    c.footer()
    return c.save(path,content)


def validate_program_asset(path,content,day):
    path=Path(path)
    with Image.open(path) as im:
        if im.size!=(1080,1920) or im.format!='JPEG':raise ValueError("Invalid program asset")
        im.verify()
    check=content.get('render_check',{})
    if not check.get('overlap_free'):raise ValueError("Missing render geometry verification")
    design=check.get('design') or ("approved_dictionary_v2" if content['slot']=='evening' else 'approved_twelve_signs_one_sheet')
    return {"passed":True,"text_fit_checked":True,"layout":{"overlap_free":True},"mobile_readability":check,"asset_bytes":path.stat().st_size,"design":design}
