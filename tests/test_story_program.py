from datetime import date,timedelta
import json
import pytest
from backend.story_program import START,DICTIONARY,SIGN_NAMES,build_program_content
import backend.story_automation_four as automation


def sky(day):
    return {"target_date":str(day),"positions":[{"planet":"太陽","longitude":165},{"planet":"月","longitude":150}],"moon":{"sign":"乙女座"},"moon_phase":{"name":"新月","illumination_percent":0},"moon_ingress":None,"major_aspects":[]}


def test_rollout_starts_with_column_not_morning_backfill():
    assert build_program_content(sky(START-timedelta(days=1)),"night") is None
    assert build_program_content(sky(START),"morning") is None
    assert build_program_content(sky(START),"noon") is None
    assert build_program_content(sky(START),"night")["content_kind"]=="column_20260907"
    assert build_program_content(sky(START),"evening")["content_kind"]=="dictionary_20260907"
    assert build_program_content(sky(START+timedelta(days=1)),"noon")["content_kind"]=="horoscope_20260907"


def test_dictionary_two_distinct_rounds_include_numerology_and_runes():
    assert len(DICTIONARY["cycle"])==7
    assert {"numerology","runes"} <= set(DICTIONARY["cycle"])
    assert "palmistry" not in DICTIONARY["cycle"]
    posts=[build_program_content(sky(START+timedelta(days=i)),"evening") for i in range(14)]
    assert len({p["headline"] for p in posts})==14
    assert [p["cycle_index"] for p in posts[:7]]==list(range(7))
    assert all(p["round_index"]==1 for p in posts[7:])


def test_twelve_signs_use_sky_positions_in_zodiac_order():
    facts=sky(START+timedelta(days=1))
    post=build_program_content(facts,"noon")
    assert [p["sign"] for p in post["items"]]==list(SIGN_NAMES)
    assert len({p["house"] for p in post["items"]})==12
    assert post["items"][5]["house"]==1
    assert post["source_positions"]==facts["positions"]
    assert post["reading_hour_jst"]==8


@pytest.mark.parametrize("slot,hour",[("morning",5),("noon",8),("night",11),("evening",17)])
def test_preview_uses_slot_hour_without_overwriting_live_record(monkeypatch,tmp_path,slot,hour):
    day=START+timedelta(days=1)
    record=tmp_path/"story_runs"/f"{day}-{slot}.json"
    record.parent.mkdir(parents=True)
    original=json.dumps({"status":"published","media_id":"existing","slot":slot})
    record.write_text(original,encoding="utf-8")
    image=tmp_path/"story_assets"/str(day)/f"{slot}.jpg"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"live-image-must-not-change")
    hours=[]
    monkeypatch.setattr(automation,"build_daily_sky",lambda target,reading_hour: hours.append(reading_hour) or sky(target))
    monkeypatch.setattr(automation,"render_slot_story",lambda *args: args[-1])
    monkeypatch.setattr(automation,"validate_story_asset",lambda *args:{"passed":True})
    monkeypatch.setattr(automation,"InstagramPublisher",lambda:pytest.fail("Preview must not contact Instagram"))
    result=automation.run_story_slot(day,slot=slot,dry_run=True,generated_root=tmp_path)
    assert hours==[hour]
    assert result["status"]=="dry_run"
    assert result["asset_url"].endswith(f"preview-{slot}.jpg")
    assert record.read_text(encoding="utf-8")==original
    assert image.read_bytes()==b"live-image-must-not-change"
    assert (record.parent/f"{day}-{slot}-preview.json").exists()


def test_published_marker_skips_before_generating_or_posting(monkeypatch,tmp_path):
    record=tmp_path/"story_runs"/f"{START}-night.json"
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps({"status":"published","media_id":"existing"}),encoding="utf-8")
    monkeypatch.setattr(automation,"build_daily_sky",lambda *args,**kwargs:pytest.fail("Already published must skip"))
    result=automation.run_story_slot(START,slot="night",generated_root=tmp_path)
    assert result["skipped"] and result["media_id"]=="existing"
