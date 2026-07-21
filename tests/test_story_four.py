from datetime import date,timedelta
from pathlib import Path
import pytest
from PIL import Image,ImageChops,ImageStat
import backend.story_automation_four as automation
from backend.story_four import SLOTS,build_slot_content,render_slot_story,solar_term
from backend.story_quality import (
    MOBILE_BODY_MIN,
    MOBILE_SUPPORT_MIN,
    MORNING_BODY_MIN,
    _decorate,
    design_variant,
    validate_layout_regions,
    validate_story_asset,
)

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
        assert report["mobile_readability"]["body_min_px"]>=34
        assert report["mobile_readability"]["support_min_px"]>=28
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

def test_night_keeps_the_restrained_legacy_decoration():
    base=Image.new("RGB",(1080,1920),(246,242,232))
    decorated=_decorate(base,date(2026,7,19),"night")
    difference=ImageChops.difference(base,decorated)
    mean=sum(ImageStat.Stat(difference).mean)/3
    assert difference.getbbox() is not None
    assert 0.5<mean<6.0

def test_mobile_readability_policy_never_shrinks_to_caption_size():
    assert MOBILE_BODY_MIN>=34
    assert MOBILE_SUPPORT_MIN>=28
    assert MORNING_BODY_MIN>=38

def test_daily_design_rotation_is_visually_detectable():
    base=Image.new("RGB",(1080,1920),(246,242,232))
    first=_decorate(base,date(2026,7,19),"evening")
    second=_decorate(base,date(2026,7,20),"evening")
    difference=ImageChops.difference(first,second)
    assert difference.getbbox() is not None
    assert sum(ImageStat.Stat(difference).mean)/3>1.5


def test_workflow_schedules_only_morning_column_and_evening():
    workflow=(Path(__file__).parents[1]/".github/workflows/daily-instagram-story.yml").read_text(encoding="utf-8")
    assert workflow.count('cron:')==9
    for cron in ('30 0 * * *','40 0 * * *','50 0 * * *'):
        assert cron in workflow
    for removed in ('15 3 * * *','25 3 * * *','35 3 * * *','30 12 * * *','40 12 * * *','50 12 * * *'):
        assert removed not in workflow
    assert '          - noon' not in workflow
    assert '          - night' not in workflow

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
