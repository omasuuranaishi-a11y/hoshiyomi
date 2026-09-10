"""User-approved four-color encyclopedia; effective September 10, 2026."""
from datetime import date
from pathlib import Path
import math
from PIL import Image
from .story_horoscope_celestial import contrast,PALETTES
from .story_dictionary_ornament import DictionarySheet as Sheet,dictionary_font as font
from .story_quality import _wrap_kinsoku,TAROT_DIR

START=date(2026,9,10)
DESIGN='approved_dictionary_astrolabe_v2'
# Extend the shared palette catalog; the horoscope still cycles only A/B.
PALETTES['C']=dict(top='#dce3da',bottom='#f1f3eb',card='#f6f7f0',rule='#becabd',ink='#303e36',gold='#556d56',muted='#617266',star='#819880',moon='#f8f5e9',glow='#e6eddf')
PALETTES['D']=dict(top='#e8dada',bottom='#f6eeea',card='#fcf5f0',rule='#d5bebe',ink='#49363d',gold='#825963',muted='#806970',star='#aa808c',moon='#fff3de',glow='#f3e4dd')

def variant_for_day(day):
    return ('C','D','A','B')[(day-START).days%4]

def graphic(s,g):
    p=s.p;d=s.d;t=g['type']
    d.rounded_rectangle((86,756,994,1060),radius=22,fill=p['card'],outline=p['rule'],width=2)
    def label(text,x,y,w=400,size=32):
        s.text(text,(x,y,x+w,y+size+8),size,'guidance',fill=p['gold'],center=True)
    if t=='moon':
        for i,angle in enumerate(g['angles']):
            cx=320+i*440;cy=863;r=66;box=(cx-r,cy-r,cx+r,cy+r)
            d.ellipse(box,fill=p['rule'])
            if angle==180:d.ellipse(box,fill=p['gold'])
            elif angle in (90,270):d.pieslice(box,-90 if angle==90 else 90,90 if angle==90 else 270,fill=p['gold'])
            s.text(g['labels'][i],(cx-160,954,cx+160,1006),40,'serif',fill=p['gold'],center=True)
        d.line((540,793,540,1023),fill=p['rule'],width=1)
    elif t=='hexagram':
        for i,v in enumerate(g['lines']):
            y=793+i*37+(14 if i>=3 else 0)
            if v:d.rectangle((170,y,430,y+15),fill=p['gold'])
            else:
                d.rectangle((170,y,278,y+15),fill=p['gold']);d.rectangle((322,y,430,y+15),fill=p['gold'])
        label('上の三本：'+g['upper'],505,817,430,38)
        label('下の三本：'+g['lower'],505,952,430,38)
    elif t=='houses':
        cx,cy,r=292,905,119
        for i in range(12):
            a=180-i*30;active=i+1 in (g['house'],g['opposite'])
            d.pieslice((cx-r,cy-r,cx+r,cy+r),a-30,a,fill=p['gold'] if active else p['rule'],outline=p['card'],width=2)
        d.ellipse((cx-68,cy-68,cx+68,cy+68),fill=p['card'])
        label(str(g['house']),cx-60,881,120,48)
        for i,(n,v) in enumerate(zip((g['house'],g['opposite']),g['labels'])):
            label('第'+str(n)+'ハウス',475,792+i*127,465,36)
            label(v,475,846+i*127,465,32)
    elif t=='number':
        label('計算例 '+g['example'],110,780,640,30)
        for i,line in enumerate(g['parts']):s.text(line,(127,831+i*45,752,873+i*45),30,'guidance')
        s.text(str(g['number']),(768,821,949,960),116,'serif',fill=p['gold'],center=True)
        label(g['sum'],110,1006,860,32)
    elif t=='runes':
        shapes=[[(0,124),(0,8),(64,-8)],[(0,124),(0,8),(68,38),(68,124)],[(0,124),(0,8),(68,36),(0,66),(69,124)]]
        for i,lines in enumerate(shapes):
            x=239+i*270
            d.line([(x+a,821+b) for a,b in lines],fill=p['gold'],width=7,joint='curve')
            if i==0:d.line((x,887,x+64,863),fill=p['gold'],width=7)
            label(('F','U','R')[i],x-55,979,175,36)
    elif t=='elements':
        for i,name in enumerate(('火','地','風','水')):
            x=110+(i%2)*445;y=781+(i//2)*137
            s.text(name,(x,y,x+66,y+51),40,'serif',fill=p['gold'])
            s.text(g['labels'][i],(x+73,y+4,x+420,y+44),30,'guidance')
            s.text(g['notes'][i],(x+73,y+62,x+420,y+101),28,'guidance',fill=p['muted'])
    elif t=='tarot':
        art=TAROT_DIR/f"major-{g['number']:02d}-rws1909-v1.jpeg"
        with Image.open(art) as original:
            im=original.convert('RGB');im.thumbnail((176,274),Image.Resampling.LANCZOS);s.im.paste(im,(151,770))
        label(g['name'],370,786,585,32)
        for i,v in enumerate(g['labels']):label(v,370,859+i*58,585,30)
    else:raise ValueError('Unsupported encyclopedia graphic '+t)

def render_dictionary(content,day,path):
    variant=variant_for_day(day);s=Sheet(variant);p=s.p
    for x,y,z in [(95,192,4),(976,190,6),(54,530,3),(1026,840,4),(54,1330,3),(991,1710,5)]:s.star(x,y,z)
    s.text(day.strftime('%Y.%m.%d')+'  /  17:00',(110,180,970,212),24,'guidance',fill=p['muted'],center=True)
    s.text('おますの',(90,224,990,285),46,'serif',fill=p['gold'],center=True)
    s.text('占い大辞典',(90,307,990,410),86,'serif',center=True)
    s.d.line((150,444,930,444),fill=p['rule'],width=2)
    s.text(content['category'],(90,477,990,528),32,'guidance',fill=p['gold'],center=True)
    for i,line in enumerate(content['headline'].splitlines()):s.text(line,(75,564+i*78,1005,637+i*78),58,'serif',center=True)
    graphic(s,content['graphic'])
    def para(value,y,size):
        for line in _wrap_kinsoku(s.d,value,font('guidance',size),856):
            s.text(line,(112,y,968,y+size+8),size,'guidance');y+=round(size*1.55)
        return y
    s.text(content['heading'],(112,1112,968,1169),40,'serif',fill=p['gold'])
    if para(content['body'],1196,38)>=1468:raise ValueError('Body exceeds region')
    s.d.line((112,1478,968,1478),fill=p['rule'],width=2)
    s.text(content['note_title'],(112,1519,968,1570),36,'serif',fill=p['gold'])
    if para(content['note'],1590,36)>=1790:raise ValueError('Note exceeds region')
    s.text('@omasu_horoscope',(100,1840,980,1885),28,'guidance',fill=p['muted'],center=True)
    for i,a in enumerate(s.boxes):
        x=a['bbox']
        if s.decor_mask.crop((math.floor(x[0])-3,math.floor(x[1])-3,math.ceil(x[2])+3,math.ceil(x[3])+3)).getbbox():raise ValueError('Decoration overlaps text: '+a['text'])
        for b in s.boxes[i+1:]:
            y=b['bbox']
            if x[0]<y[2] and x[2]>y[0] and x[1]<y[3] and x[3]>y[1]:raise ValueError('Text overlap')
    if contrast(p['ink'],p['card'])<7:raise ValueError('Low contrast')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);s.im.save(path,'JPEG',quality=96,subsampling=0)
    content['design_variant']='dictionary_celestial_'+variant
    content['render_check']=dict(design=DESIGN,variant=variant,rotation='daily_four_colors',overlap_free=True,decoration_overlap_free=True,body_px=38,note_px=36,minimum_px=28,body_font='Noto Sans JP',title_font='Kaisei Tokumin Medium',text_regions=len(s.boxes))
    return path
