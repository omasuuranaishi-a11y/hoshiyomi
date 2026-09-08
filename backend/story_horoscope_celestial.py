"""Approved celestial twelve-sign layout; bundled fonts, no network or posting calls."""
from pathlib import Path
from datetime import date
import re, math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

FONT_ROOT=Path(__file__).resolve().parent/"assets"/"fonts"
GLYPHS="♈♉♊♋♌♍♎♏♐♑♒♓"
START=date(2026,9,9)
DESIGN_VERSION="approved_twelve_signs_celestial_v5"
PALETTES={
 'A':dict(top='#0c172b',bottom='#24324b',card='#18273f',rule='#425169',ink='#f2f3f6',gold='#dbbf8e',muted='#b3becf',star='#d7c19d',moon='#e1c695',glow='#385979'),
 'B':dict(top='#d8d8ea',bottom='#f0eef7',card='#faf9fc',rule='#d3cfdf',ink='#313a50',gold='#746084',muted='#646d83',star='#897697',moon='#fbf7ec',glow='#ece6f5'),
}


def font(kind,size):
    if kind=='serif':
        f=ImageFont.truetype(str(FONT_ROOT/'NotoSerifJP-VF.ttf'),size)
        f.set_variation_by_axes([600])
        return f
    if kind=='symbol':
        f=ImageFont.truetype(str(FONT_ROOT/'NotoSansSymbols-VF.ttf'),size)
        f.set_variation_by_axes([400])
        return f
    if kind=='guidance':
        f=ImageFont.truetype(str(FONT_ROOT/'NotoSansJP-VF.ttf'),size)
        f.set_variation_by_axes([400])
        return f
    return ImageFont.truetype(str(FONT_ROOT/'BIZUDGothic-Regular.ttf'),size)


def variant_for_day(day):
    """Approved daily A/B cycle, stable across month boundaries and re-renders."""
    return ('A','B')[(day-START).days%2]


def luminance(color):
    values=Image.new('RGB',(1,1),color).getpixel((0,0))
    values=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in values]
    return sum(a*b for a,b in zip(values,(.2126,.7152,.0722)))


def contrast(a,b):
    x,y=sorted((luminance(a),luminance(b)))
    return (y+.05)/(x+.05)


class Sheet:
    def __init__(self,variant):
        self.variant=variant;self.p=PALETTES[variant];self.boxes=[]
        self.decor_mask=Image.new('L',(1080,1920),0)
        gradient=Image.linear_gradient('L').resize((1080,1920))
        self.im=ImageOps.colorize(gradient,self.p['top'],self.p['bottom'])
        glow=Image.new('RGBA',self.im.size)
        ImageDraw.Draw(glow).ellipse((610,70,1100,540),fill=self.p['glow']+'65')
        self.im=Image.alpha_composite(self.im.convert('RGBA'),glow.filter(ImageFilter.GaussianBlur(95))).convert('RGB')
        self.d=ImageDraw.Draw(self.im)

    def text(self,value,box,size,kind='body',fill=None,center=False):
        x,y,r,b=box;f=font(kind,size)
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

    def star(self,x,y,size=5):
        color=self.p['star']
        ImageDraw.Draw(self.decor_mask).rectangle((x-size,y-size,x+size,y+size),fill=255)
        if size<3:self.d.ellipse((x-size,y-size,x+size,y+size),fill=color);return
        self.d.polygon(((x,y-size),(x+size*.22,y-size*.22),(x+size,y),(x+size*.22,y+size*.22),(x,y+size),(x-size*.22,y+size*.22),(x-size,y),(x-size*.22,y-size*.22)),fill=color)

    def decorate(self):
        # Decorative lunar crescent, deliberately outside every text box.
        mask=Image.new('L',self.im.size,0);m=ImageDraw.Draw(mask)
        m.ellipse((816,231,967,382),fill=255)
        m.ellipse((851,214,996,359),fill=0)
        self.decor_mask=mask.copy()
        self.im.paste(self.p['moon'],mask=mask);self.d=ImageDraw.Draw(self.im)
        self.d.arc((744,189,1024,431),215,294,fill=self.p['rule'],width=2)
        ImageDraw.Draw(self.decor_mask).arc((744,189,1024,431),215,294,fill=255,width=2)
        for x,y,s in [(725,236,7),(1010,239,4),(766,359,5),(983,406,2),(694,421,2),(984,172,3),(39,562,2),(1041,711,4),(40,1053,2),(1040,1277,2),(36,1495,3),(1040,1578,3),(745,1774,7),(791,1810,2),(308,1793,3)]:self.star(x,y,s)
        # Faint short decorative constellation in the quiet footer.
        self.d.line(((834,1772),(886,1733),(936,1770),(1006,1737)),fill=self.p['rule'],width=2)
        ImageDraw.Draw(self.decor_mask).line(((834,1772),(886,1733),(936,1770),(1006,1737)),fill=255,width=2)
        for x,y in [(834,1772),(886,1733),(936,1770),(1006,1737)]:self.star(x,y,2)

    def render(self,content,day,path):
        p=self.p;self.decorate()
        self.text(day.strftime('%Y.%m.%d')+'  '+('MON','TUE','WED','THU','FRI','SAT','SUN')[day.weekday()],(70,148,575,191),32,fill=p['muted'])
        self.text('08:00',(702,148,957,191),28,fill=p['muted'])
        self.text('12星座',(70,227,1010,334),94,'serif',fill=p['gold'],center=True)
        self.text('きょうの運勢',(70,345,1010,430),66,'serif',center=True)
        self.d.line((71,458,1009,458),fill=p['rule'],width=2)
        self.text('星の流れを、今日のひとつのヒントに。',(70,475,1010,519),28,fill=p['muted'],center=True)
        lines_report=[]
        for i,item in enumerate(content['items']):
            x=68+(i%2)*484;y=543+(i//2)*188
            self.d.rounded_rectangle((x,y,x+460,y+175),radius=14,fill=p['card'])
            self.d.line((x+22,y+72,x+438,y+72),fill=p['rule'],width=1)
            symbol_width=self.d.textlength(GLYPHS[i],font=font('symbol',40))
            sign_width=self.d.textlength(item['sign'],font=font('serif',48))
            sign_left=x+230-sign_width/2
            symbol_left=sign_left-18-symbol_width
            self.text(GLYPHS[i],(symbol_left,y+18,symbol_left+symbol_width+1,y+64),40,'symbol',fill=p['gold'])
            self.text(item['sign'],(x+22,y+15,x+438,y+68),48,'serif',fill=p['gold'],center=True)
            label_center=(self.boxes[-1]['bbox'][0]+self.boxes[-1]['bbox'][2])/2
            name_center_offset=label_center-(x+230)
            assert abs(name_center_offset)<=1, f'Sign name is not centered: {item["sign"]}'
            lines=[s.strip() for s in re.split(r'(?<=[。！？])|\n',item['text']) if s.strip()]
            if len(lines)!=2:raise ValueError('Horoscope must have two complete sentences')
            item['rendered_lines']=lines
            for j,line in enumerate(lines):self.text(line,(x+22,y+86+j*45,x+438,y+130+j*45),40,'guidance',center=True)
            lines_report.append(dict(sign=item['sign'],lines=lines,alignment='center',sign_name_centered=True,sign_name_center_offset_px=name_center_offset))
        self.text('太陽星座をもとにした一般向けの運勢',(70,1693,1010,1737),28,fill=p['muted'],center=True)
        self.text('OMASU HOROSCOPE',(70,1781,1010,1825),30,'serif',fill=p['gold'],center=True)
        self.text('@omasu_horoscope',(70,1838,1010,1880),28,fill=p['muted'],center=True)
        for i,a in enumerate(self.boxes):
            x=a['bbox']
            padded=(math.floor(x[0])-4,math.floor(x[1])-4,math.ceil(x[2])+4,math.ceil(x[3])+4)
            if self.decor_mask.crop(padded).getbbox():raise ValueError(f'Decoration near text: {a["text"]}')
            for b in self.boxes[i+1:]:
                y=b['bbox']
                if x[0]<y[2] and x[2]>y[0] and x[1]<y[3] and x[3]>y[1]:raise ValueError(f'Text overlap {a["text"]} / {b["text"]}')
        assert contrast(p['ink'],p['card'])>=7
        assert contrast(p['gold'],p['card'])>=4.5
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        self.im.save(path,"JPEG",quality=96,subsampling=0)
        content["design_variant"]="celestial_"+("midnight" if self.variant=="A" else "moonrise")
        content["render_check"]=dict(
            design=DESIGN_VERSION,variant=self.variant,rotation="daily_alternating",
            overlap_free=True,decoration_overlap_free=True,title_centered=True,
            sign_names_centered=True,body_alignment="center",body_px=40,
            body_font="Noto Sans JP",body_weight=400,sign_px=48,
            sign_font="Noto Serif JP",sign_weight=600,minimum_px=28,
            linebreak_policy="one_sentence_per_line_v1",text_regions=len(self.boxes),
            contrast=round(contrast(p["ink"],p["card"]),2),
            sign_contrast=round(contrast(p["gold"],p["card"]),2),items=lines_report,
        )
        return path


def render_celestial_horoscope(content,day,path):
    return Sheet(variant_for_day(day)).render(content,day,path)
