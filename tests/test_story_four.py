from datetime import date,timedelta
import pytest
import backend.story_automation_four as automation
from backend.story_four import SLOTS,build_slot_content,render_slot_story,solar_term
from backend.story_quality import design_variant,validate_layout_regions,validate_story_asset

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
        report=validate_story_asset(path,item,day)
        assert report["passed"] and report["layout"]["overlap_free"]
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

def test_important_text_regions_are_safe_and_overlap_free():
    for slot in SLOTS:
        report=validate_layout_regions(slot)
        assert report["overlap_free"]
        assert report["safe_bottom"]<=1680

def test_exact_design_combinations_do_not_repeat_for_28_days():
    for slot in SLOTS:
        names=[design_variant(date(2026,7,17)+timedelta(days=i),slot)["name"] for i in range(28)]
        assert len(set(names))==28

def test_quality_failure_never_reaches_instagram(monkeypatch,tmp_path):
    published=[]
    monkeypatch.setattr(automation,"build_daily_sky",lambda *args,**kwargs: facts(date(2026,7,18)))
    monkeypatch.setattr(
        automation,
        "build_slot_content",
        lambda sky,slot: {"slot":slot,"title":"test"},
    )
    monkeypatch.setattr(automation,"render_slot_story",lambda *args,**kwargs: args[-1])

    def reject_asset(*args,**kwargs):
        raise RuntimeError("simulated overlapping text")

    class Publisher:
        def publish_story(self,url):
            published.append(url)
            return "unexpected"

    monkeypatch.setattr(automation,"validate_story_asset",reject_asset)
    monkeypatch.setattr(automation,"InstagramPublisher",Publisher)
    monkeypatch.setattr(automation,"_notify_failure",lambda *args,**kwargs: None)

    with pytest.raises(RuntimeError,match="overlapping text"):
        automation.run_story_slot(
            date(2026,7,18),slot="evening",generated_root=tmp_path
        )

    assert published==[]
