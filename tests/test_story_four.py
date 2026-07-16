from datetime import date,timedelta
from backend.story_four import SLOTS,build_slot_content,render_slot_story,solar_term
from backend.story_quality import design_variant

def facts(day=date(2026,7,17)):
    moon_degree=(day.toordinal()*13.176)%30
    return {"target_date":day.isoformat(),"positions":[{"planet":"太陽","longitude":114.2},{"planet":"月","longitude":150+moon_degree}],"moon":{"planet":"月","sign":"乙女座","degree_in_sign":moon_degree,"longitude":150+moon_degree},"moon_phase":{"name":"満ちていく三日月","illumination_percent":8.7},"moon_ingress":{"from":"獅子座","to":"乙女座","local_time":"09:07"},"major_aspects":[{"planets":["月","金星"],"aspect":"セクスタイル","orb":1.2}]}

def test_four_slots_render(tmp_path):
    day=date(2026,7,17);items=[build_slot_content(facts(day),s) for s in SLOTS]
    assert len({x["title"] for x in items})==4
    assert solar_term(facts(day))=="小暑"
    for item in items:
        path=render_slot_story(item,day,tmp_path/f"{item['slot']}.jpg")
        assert path.stat().st_size>150000
        from PIL import Image
        with Image.open(path) as image:
            assert image.size == (1080, 1920)

def test_content_never_repeats_for_sample_period():
    seen=set()
    for offset in range(120):
        day=date(2026,7,17)+timedelta(days=offset)
        signature=tuple(str(build_slot_content(facts(day),s)) for s in SLOTS)
        assert signature not in seen
        seen.add(signature)

def test_seven_designs_rotate_without_consecutive_repeats():
    for slot in SLOTS:
        names=[design_variant(date(2026,7,17)+timedelta(days=i),slot)["name"] for i in range(7)]
        assert len(set(names))==7
        assert all(left!=right for left,right in zip(names,names[1:]))
