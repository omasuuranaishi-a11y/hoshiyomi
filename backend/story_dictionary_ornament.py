"""Approved encyclopedia ornament and heading font, isolated from horoscope."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import math
from .story_horoscope_celestial import Sheet as BaseSheet,font as base_font,GLYPHS

def dictionary_font(kind,size):
    if kind=='serif':
        return ImageFont.truetype(str(Path(__file__).parent/'assets/fonts/KaiseiTokumin-Medium.ttf'),size)
    return base_font(kind,size)

def decorate(self,variant):
    # Code-native ornament: antique astronomical plate, quiet reading field.
    d=self.d;gold='#aaa783' if variant!='A' else '#a9956c';faint='#c5cbb9' if variant!='A' else '#425169'
    d.rounded_rectangle((29,31,1051,1889),radius=190,outline=gold,width=2)
    d.rounded_rectangle((43,45,1037,1875),radius=179,outline=faint,width=1)
    # Moon-and-star seal with engraved rays, complete inside the upper margin.
    gold='#96936b' if variant!='A' else '#c2ab7c'
    for r in (51,65):d.ellipse((540-r,88-r,540+r,88+r),outline=gold,width=2)
    for i in range(32):
        a=math.radians(i*11.25);r=70;end=82 if i%4==0 else 75
        d.line((540+r*math.cos(a),88+r*math.sin(a),540+end*math.cos(a),88+end*math.sin(a)),fill=gold,width=2)
    moon=Image.new('L',self.im.size,0);md=ImageDraw.Draw(moon)
    md.ellipse((510,58,568,117),fill=255);md.ellipse((528,48,580,105),fill=0)
    self.im.paste(gold,mask=moon)
    d.polygon(((560,66),(563,76),(573,79),(563,82),(560,92),(557,82),(547,79),(557,76)),fill=gold)
    for left in (True,False):
        points=[(327,84),(366,66),(405,99),(447,79)]
        if not left:points=[(1080-x,y) for x,y in points]
        d.line(points,fill=gold,width=1)
        for x,y in points:d.ellipse((x-3,y-3,x+3,y+3),fill=gold)
    # Thin arc fragments at the outer edges evoke a celestial atlas.
    for cx,cy in ((-125,510),(1205,1385)):
        for r in (206,221,244):d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=faint,width=1)
    # Zodiac fragments stay in the gutters, away from the reading column.
    for cx,cy in ((-150,515),(1230,1375)):
        for i in range(12):
            a=math.radians(i*30)
            d.line((cx+180*math.cos(a),cy+180*math.sin(a),cx+250*math.cos(a),cy+250*math.sin(a)),fill=faint,width=1)
            x=cx+213*math.cos(a);y=cy+213*math.sin(a)
            if 45<x<90 or 990<x<1035:d.text((x,y),GLYPHS[i],font=base_font('symbol',25),fill=gold,anchor='mm')
    # Symmetrical foliate corners suggest a vintage divination book cover.
    for right in (False,True):
        for bottom in (False,True):
            def pt(x,y):return (1080-x if right else x,1920-y if bottom else y)
            d.line([pt(75,194),pt(99,152),pt(135,116),pt(187,85)],fill=gold,width=2)
            for x,y in ((100,150),(126,124),(158,102)):
                d.line([pt(x,y),pt(x-18,y-25),pt(x-10,y-36),pt(x,y)],fill=gold,width=1)
                d.line([pt(x,y),pt(x+30,y+2),pt(x+39,y-6),pt(x,y)],fill=gold,width=1)
    # Fine engraved diamonds and tiny dots, deliberately limited to gutters.
    for x in (64,1016):
        for y in (695,1120,1465,1790):
            d.polygon(((x,y-8),(x+4,y),(x,y+8),(x-4,y)),outline=gold)
    # Seven small moon phases in the empty lower margin.
    for i in range(7):
        x=360+i*60;y=1795;r=10
        d.ellipse((x-r,y-r,x+r,y+r),outline=gold,width=1)
        if i in (1,2):d.pieslice((x-r,y-r,x+r,y+r),-90,90,fill=gold)
        elif i==3:d.ellipse((x-r,y-r,x+r,y+r),fill=gold)
        elif i in (4,5):d.pieslice((x-r,y-r,x+r,y+r),90,270,fill=gold)
    # Record ornament geometry for the renderer's text collision guard.
    mask=Image.new('L',self.im.size,0);m=ImageDraw.Draw(mask)
    m.rectangle((430,0,650,155),fill=255)
    for x in (64,1016):
        for y in (695,1120,1465,1790):m.rectangle((x-5,y-9,x+5,y+9),fill=255)
    m.rectangle((349,1784,731,1806),fill=255)
    self.decor_mask=mask
class DictionarySheet(BaseSheet):
    def __init__(self,variant):
        super().__init__(variant)
        before=self.im.copy()
        decorate(self,variant)
        # All ornament pixels are guarded, not just a manually selected subset.
        from PIL import ImageChops
        self.decor_mask=ImageChops.difference(before,self.im).convert('L').point(lambda x:255 if x else 0)

    def text(self,value,box,size,kind='body',fill=None,center=False):
        x,y,r,b=box;f=dictionary_font(kind,size)
        width=self.d.textlength(value,font=f)
        if width>r-x+.5:raise ValueError(f'Width overflow: {value}: {width}>{r-x}')
        center_x=(x+r)/2
        if center:x=center_x-width/2
        ink=self.d.textbbox((x,y),value,font=f,anchor='lt')
        if ink[3]>b or ink[2]>r+.5:raise ValueError(f'Ink outside box: {value}')
        self.d.text((x,y),value,font=f,anchor='lt',fill=fill or self.p['ink'])
        if center and abs((ink[0]+ink[2])/2-center_x)>1:
            raise ValueError(f'Center alignment mismatch: {value}')
        self.boxes.append(dict(text=value,bbox=ink,size=size,font=kind,alignment='center' if center else 'left'))

