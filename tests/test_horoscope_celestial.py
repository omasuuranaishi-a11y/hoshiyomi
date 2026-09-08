from copy import deepcopy
from datetime import date,timedelta
from PIL import Image,ImageDraw
import pytest
from backend.story_horoscope_celestial import START,DESIGN_VERSION,GLYPHS,Sheet,font,variant_for_day
from backend.story_program import HOUSE_OPENINGS,HOUSE_ACTIONS,SIGN_NAMES,build_program_content
from backend.story_program_render import render_program,validate_program_asset


def content_for(day):
    return build_program_content({'target_date':str(day),'moon':{'sign':'獅子座'},'positions':[],'major_aspects':[]},'noon')


def test_rotation_is_deterministic_through_month_year_and_leap_boundaries():
    assert variant_for_day(START)=='A'
    assert variant_for_day(START+timedelta(days=1))=='B'
    days=[START+timedelta(days=i) for i in range(1100)]
    assert all(variant_for_day(a)!=variant_for_day(b) for a,b in zip(days,days[1:]))
    assert all(variant_for_day(d)==variant_for_day(date.fromisoformat(str(d))) for d in days)


def test_all_current_copy_fits_at_40px_and_all_zodiac_symbols_exist():
    d=ImageDraw.Draw(Image.new('RGB',(1080,1920)))
    f=font('guidance',40)
    phrases=list(HOUSE_OPENINGS)+[p for actions in HOUSE_ACTIONS for p in actions]
    assert all(d.textlength(p,font=f)<=416 for p in phrases)
    symbols=font('symbol',40)
    masks=[bytes(symbols.getmask(g)) for g in GLYPHS]
    assert len(set(masks))==12
    assert bytes(symbols.getmask('\uffff')) not in masks


@pytest.mark.parametrize('variant',('A','B'))
@pytest.mark.parametrize('mode',range(3))
def test_both_palettes_center_names_without_symbols_and_preserve_complete_sentences(tmp_path,variant,mode):
    content=content_for(START)
    for i,item in enumerate(content['items']):
        item['text']=HOUSE_OPENINGS[i]+HOUSE_ACTIONS[i][mode]
    original=deepcopy(content)
    sheet=Sheet(variant)
    path=sheet.render(content,START,tmp_path/f'{variant}-{mode}.jpg')
    with Image.open(path) as im:
        assert im.size==(1080,1920) and im.format=='JPEG'
    report=content['render_check']
    assert report['design']==DESIGN_VERSION
    assert report['title_centered'] and report['decoration_overlap_free']
    assert report['sign_names_centered'] and report['body_alignment']=='center'
    assert report['body_px']==40 and report['sign_px']==48
    for i,item in enumerate(report['items']):
        assert abs(item['sign_name_center_offset_px'])<=1
        assert item['lines']==[HOUSE_OPENINGS[i],HOUSE_ACTIONS[i][mode]]
        assert content['items'][i]['text']==original['items'][i]['text']
        bbox=next(b['bbox'] for b in sheet.boxes if b['text']==SIGN_NAMES[i])
        assert abs((bbox[0]+bbox[2])/2-(68+(i%2)*484+230))<=1
    for title in ('12星座','きょうの運勢'):
        bbox=next(b['bbox'] for b in sheet.boxes if b['text']==title)
        assert abs((bbox[0]+bbox[2])/2-540)<=1
    assert validate_program_asset(path,content,START)['design']==DESIGN_VERSION


def test_activation_date_and_repeat_renders(tmp_path):
    old=content_for(date(2026,9,8))
    render_program(old,date(2026,9,8),tmp_path/'before.jpg')
    assert old['render_check']['body_px']==38
    for offset,expected in ((0,'A'),(1,'B')):
        day=START+timedelta(days=offset)
        first,second=content_for(day),content_for(day)
        one=render_program(first,day,tmp_path/f'{offset}-one.jpg')
        two=render_program(second,day,tmp_path/f'{offset}-two.jpg')
        assert one.read_bytes()==two.read_bytes()
        assert first['render_check']['variant']==expected


def test_dictionary_does_not_use_new_horoscope_renderer(monkeypatch,tmp_path):
    import backend.story_horoscope_celestial as celestial
    monkeypatch.setattr(celestial,'render_celestial_horoscope',lambda *a:pytest.fail('Dictionary must not change'))
    facts={'target_date':str(START),'moon':{'sign':'獅子座'},'positions':[],'major_aspects':[]}
    content=build_program_content(facts,'evening')
    path=render_program(content,START,tmp_path/'dictionary.jpg')
    assert validate_program_asset(path,content,START)['design']=='approved_dictionary_v2'
