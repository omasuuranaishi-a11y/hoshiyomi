from datetime import date
import pytest
from PIL import Image,ImageDraw,ImageFont
from backend.story_program import HOUSE_OPENINGS,HOUSE_ACTIONS,SIGN_NAMES,build_program_content
from backend.story_program_render import Canvas,_wrap_horoscope_sentences,render_program,validate_program_asset
from backend.story_quality import FONT_DIR,_wrap_kinsoku


@pytest.fixture
def metrics():
    return ImageDraw.Draw(Image.new("RGB",(1080,1920))),ImageFont.truetype(str(FONT_DIR/"ZenMaruGothic-Regular.ttf"),38)


@pytest.mark.parametrize("house",range(12))
@pytest.mark.parametrize("mode",range(3))
def test_all_current_horoscopes_keep_sentences_on_two_complete_lines(metrics,house,mode):
    draw,font=metrics
    expected=[HOUSE_OPENINGS[house],HOUSE_ACTIONS[house][mode]]
    lines=_wrap_horoscope_sentences(draw,"".join(expected),font,405)
    assert lines==expected
    assert len(lines)==2
    assert all(draw.textlength(line,font=font)<=405 for line in lines)
    assert all(len(line.rstrip("。！？"))>=4 for line in lines)


@pytest.mark.parametrize("text,expected",[
    ("好きなことが入口。ひらめきを形に。",["好きなことが入口。","ひらめきを形に。"]),
    ("自分らしさが主役。今の好みを装いに。",["自分らしさが主役。","今の好みを装いに。"]),
    ("好奇心が次の扉に。未知の分野の本へ。",["好奇心が次の扉に。","未知の分野の本へ。"]),
    ("信頼を育てる時間。身近な相手に相談。",["信頼を育てる時間。","身近な相手に相談。"]),
    ("好きなことが入口。\nひらめきを形に。",["好きなことが入口。","ひらめきを形に。"]),
])
def test_reported_split_words_and_existing_linebreaks(metrics,text,expected):
    draw,font=metrics
    assert _wrap_horoscope_sentences(draw,text,font,405)==expected


def test_default_dictionary_wrapping_is_unchanged(metrics):
    draw,font=metrics
    text="好きなことが入口。ひらめきを形に。"
    c=Canvas("#496e74","#e4ece7")
    assert c.text(text,(100,200,505,500),38)==_wrap_kinsoku(draw,text,font,405)


def test_full_sheet_preserves_text_size_and_reports_actual_lines(tmp_path):
    day=date(2026,9,9)
    facts={"target_date":str(day),"moon":{"sign":"獅子座"},"positions":[],"major_aspects":[]}
    content=build_program_content(facts,"noon")
    original=[item['text'] for item in content['items']]
    path=render_program(content,day,tmp_path/'horoscope.jpg')
    assert validate_program_asset(path,content,day)['passed']
    assert content['render_check']['body_px']==38
    assert content['render_check']['linebreak_policy']=='one_sentence_per_line_v1'
    assert [item['text'] for item in content['items']]==original
    assert [item['sign'] for item in content['items']]==list(SIGN_NAMES)
    assert all(len(item['rendered_lines'])==2 for item in content['items'])
    assert all(''.join(item['rendered_lines'])==item['text'] for item in content['items'])
