from datetime import date,timedelta
from pathlib import Path
import pytest
from PIL import Image,ImageChops,ImageDraw,ImageStat
import backend.story_automation_four as automation
from backend.story_four import SLOTS,TAROT_REFRESH_DATE,TAROT_START_DATE,TAROT_POSTS,TAROT_TOPICS,build_slot_content,render_slot_story,solar_term,validate_content_depth
from backend.story_quality import (
    MOBILE_BODY_MIN,
    MOBILE_SUPPORT_MIN,
    MORNING_BODY_MIN,
    _apply_daily_palette,
    _decorate,
    _gothic_font,
    _handwritten_gothic_font,
    _wrap_kinsoku,
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

def test_daily_life_scenes_rotate_for_twenty_four_days():
    for slot in ("morning","night"):
        keys=[]
        for offset in range(24):
            day=date(2026,7,17)+timedelta(days=offset)
            keys.append(build_slot_content(facts(day),slot)["scene_key"])
        assert len(set(keys))==24

def test_three_daily_posts_never_repeat_the_same_scene():
    for offset in range(60):
        day=date(2026,7,17)+timedelta(days=offset)
        keys=[build_slot_content(facts(day),slot)["scene_key"] for slot in ("morning","night","evening")]
        assert len(set(keys))==3

def test_scheduled_copy_has_daily_life_and_reasoning_depth():
    for offset in range(60):
        day=date(2026,7,17)+timedelta(days=offset)
        for slot in ("morning","night","evening"):
            report=validate_content_depth(build_slot_content(facts(day),slot))
            assert report["passed"]
            # Approved programs no longer reject prose based on keyword depth.
            expected_new = day >= date(2026,9,7) and (slot != "morning" or day > date(2026,9,7))
            assert report["checked"] is (not expected_new)

def test_morning_translates_the_supplied_sky_into_reasoning_and_action():
    item=build_slot_content(facts(date(2026,8,15)),"morning")
    assert "月と金星のセクスタイル" in item["hint"]
    assert "月相の視点" not in item["hint"]
    assert "最初の一手" in item["thinking"]
    assert "\n" not in item["thinking"]
    assert not any(label in item["thinking"] for label in ("考え方｜","動き方｜","問い｜"))
    assert validate_content_depth(item)["passed"]

def test_column_reads_as_one_article_with_three_spaced_paragraphs():
    item=build_slot_content(facts(date(2026,8,10)),"night")
    body=item["column"]
    assert item["paragraphs"]==body.split("\n\n")
    assert len(item["paragraphs"])==3
    assert body.count("\n\n")==2
    assert all("\n" not in paragraph for paragraph in item["paragraphs"])
    assert len(body)>=180
    assert not any(label in body for label in ("星の読み｜","日常の場面｜","考え方｜","判断基準｜","最初の一手｜","今日の一手｜","次回｜"))
    assert "ending" not in item
    assert validate_content_depth(item)["passed"]

def test_all_twenty_four_columns_have_distinct_substance_and_no_item_labels():
    columns=[]
    for offset in range(24):
        day=date(2026,7,17)+timedelta(days=offset)
        item=build_slot_content(facts(day),"night")
        columns.append(item["column"])
        assert len(item["column"])>=180
        assert item["column"].count("\n\n")==2
        assert "｜" not in item["column"]
        assert validate_content_depth(item)["passed"]
    assert len(set(columns))==24

def test_column_line_wrapping_never_exceeds_the_text_box():
    image=Image.new("RGB",(1080,1920),"white")
    draw=ImageDraw.Draw(image)
    font=_gothic_font(41)
    item=build_slot_content(facts(date(2026,8,10)),"night")
    lines=_wrap_kinsoku(draw,item["column"],font,910)
    assert all(draw.textlength(line,font=font)<=910 for line in lines)

def test_evening_changes_from_maintenance_to_tarot_on_august_fifteenth():
    last_maintenance=build_slot_content(facts(TAROT_START_DATE-timedelta(days=1)),"evening")
    first_tarot=build_slot_content(facts(TAROT_START_DATE),"evening")
    assert last_maintenance["title"]=="星よみメンテナンス"
    assert first_tarot["title"]=="タロットノート"
    assert first_tarot["card_name"]=="愚者"
    assert first_tarot["content_kind"]=="tarot_knowledge"
    assert not ({"question","next_card","series_day"} & first_tarot.keys())

def test_tarot_topics_cover_general_knowledge_without_a_sequential_card_teaser():
    topics=[]
    card_numbers=[]
    for offset in range(len(TAROT_TOPICS)):
        item=build_slot_content(facts(TAROT_START_DATE+timedelta(days=offset)),"evening")
        topics.append(item["topic_key"])
        card_numbers.append(item["card_number"])
        assert item["notes"]
        assert item["origin"]
        assert item["core"]
        assert item["method"]
        assert item["humor"]
        assert "カードは黙っています" not in item["humor"]
        assert not ({"question","next_card","series_day"} & item.keys())
        assert validate_content_depth(item)["passed"]
    assert len(set(topics))==len(TAROT_TOPICS)
    assert card_numbers[:3] != [0,1,2]

def test_refreshed_tarot_rotation_starts_with_a_comparison_and_keeps_real_card_art():
    item=build_slot_content(facts(TAROT_REFRESH_DATE),"evening")
    assert item["content_kind"]=="tarot_insight"
    assert item["format"]=="comparison"
    assert item["card_numbers"]==[11,4]
    assert item["headline"]=="同じ『決める』でも、\n何が違う？"
    assert len(item["points"])==2
    assert validate_content_depth(item)["passed"]

def test_legacy_tarot_rotation_balances_knowledge_and_reading_formats(monkeypatch):
    import backend.story_program as program
    monkeypatch.setattr(program,"START",date(2099,1,1))
    formats=[];keys=[]
    for offset in range(len(TAROT_POSTS)):
        item=build_slot_content(facts(TAROT_REFRESH_DATE+timedelta(days=offset)),"evening")
        formats.append(item["format"]);keys.append(item["post_key"])
        assert 1<=len(item["card_numbers"])<=3
        assert len(item["card_numbers"])==len(item["card_labels"])
        assert validate_content_depth(item)["passed"]
    assert set(formats)=={"comparison","daily","symbol","choice","spread"}
    assert len(set(keys))==len(TAROT_POSTS)
    assert all(left!=right for left,right in zip(formats,formats[1:]))

def test_refreshed_tarot_renders_one_two_and_three_card_formats(tmp_path):
    for day in (TAROT_REFRESH_DATE,TAROT_REFRESH_DATE+timedelta(days=1),TAROT_REFRESH_DATE+timedelta(days=2)):
        item=build_slot_content(facts(day),"evening")
        path=render_slot_story(item,day,tmp_path/f"{item['post_key']}.jpg")
        report=validate_story_asset(path,item,day)
        assert report["passed"]
        assert report["tarot_card_art"]["card_numbers"]==item["card_numbers"]

def test_seven_designs_rotate_without_consecutive_repeats():
    for slot in SLOTS:
        names=[design_variant(date(2026,7,17)+timedelta(days=i),slot)["name"] for i in range(7)]
        assert len(set(names))==7
        assert all(left!=right for left,right in zip(names,names[1:]))
        motifs=[design_variant(date(2026,7,17)+timedelta(days=i),slot)["motif_index"] for i in range(7)]
        assert all(left!=right for left,right in zip(motifs,motifs[1:]))

def test_important_text_regions_are_safe_and_overlap_free():
    for slot in SLOTS:
        report=validate_layout_regions(slot)
        assert report["overlap_free"]
        assert report["safe_bottom"]<=1680

def test_exact_design_combinations_do_not_repeat_for_28_days():
    for slot in SLOTS:
        names=[design_variant(date(2026,7,17)+timedelta(days=i),slot)["name"] for i in range(28)]
        assert len(set(names))==28

def test_column_decoration_stays_tasteful_while_changing_daily():
    base=Image.new("RGB",(1080,1920),(246,242,232))
    decorated=_decorate(base,date(2026,7,19),"night")
    difference=ImageChops.difference(base,decorated)
    mean=sum(ImageStat.Stat(difference).mean)/3
    assert difference.getbbox() is not None
    assert 5.0<mean<15.0

def test_night_edge_circle_never_enters_the_column_text_area():
    start=date(2026,7,19)
    day=next(start+timedelta(days=offset) for offset in range(28) if design_variant(start+timedelta(days=offset),"night")["motif_index"]==2)
    base=Image.new("RGB",(1080,1920),(246,242,232))
    theme=design_variant(day,"night")
    tint=Image.blend(base,Image.new("RGB",base.size,theme["primary"]),0.055)
    decorated=_decorate(base,day,"night")
    motif_only=ImageChops.difference(tint,decorated)
    # The user asked to remove the circle entirely; absence is intentional.
    assert motif_only.getbbox() is None
    assert motif_only.crop((85,900,995,1680)).getbbox() is None

def test_large_left_circle_and_dots_are_removed_from_every_slot():
    start=date(2026,7,19)
    for slot in ("morning","evening","night"):
        day=next(start+timedelta(days=offset) for offset in range(28) if design_variant(start+timedelta(days=offset),slot)["motif_index"]==2)
        base=Image.new("RGB",(1080,1920),(246,242,232))
        theme=design_variant(day,slot)
        tint_amount=.055 if slot=="night" else .075
        tinted=Image.blend(base,Image.new("RGB",base.size,theme["primary"]),tint_amount)
        decorated=_decorate(base,day,slot)
        # Rounded border may remain at x=18; the deleted circle occupied x=60..120.
        assert ImageChops.difference(tinted,decorated).crop((60,1200,125,1680)).getbbox() is None

def test_column_title_uses_the_bundled_rounded_handwritten_font():
    family,_style=_handwritten_gothic_font(48).getname()
    assert "Klee" in family

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


def test_morning_palette_changes_are_obvious_on_a_phone():
    base=Image.new("RGB",(1080,1920),(246,242,232))
    days=[date(2026,7,24)+timedelta(days=i) for i in range(4)]
    images=[_decorate(_apply_daily_palette(base,day,"morning"),day,"morning") for day in days]
    for left,right in zip(images,images[1:]):
        difference=ImageChops.difference(left,right)
        assert difference.getbbox() is not None
        # The daily palette stays visibly different while respecting the masthead safe area.
        assert sum(ImageStat.Stat(difference).mean)/3>5.0
        grayscale=difference.convert("L")
        histogram=grayscale.histogram()
        changed=sum(histogram[12:])/(1080*1920)
        assert changed>0.08

def test_workflow_schedules_four_programs_with_three_chances_each():
    workflow=(Path(__file__).parents[1]/".github/workflows/daily-instagram-story.yml").read_text(encoding="utf-8")
    assert workflow.count('cron:')==12
    for cron in ('43 17 * * *','31 18 * * *','19 19 * * *','55 22 * * *','10 23 * * *','25 23 * * *','55 1 * * *','10 2 * * *','25 2 * * *','55 7 * * *','10 8 * * *','25 8 * * *'):
        assert cron in workflow
    for removed in ('58 20 * * *','8 21 * * *','18 21 * * *','30 0 * * *','40 0 * * *','50 0 * * *','30 9 * * *','40 9 * * *','50 9 * * *','11 0 * * *','11 9 * * *'):
        assert removed not in workflow
    assert 'PUBLISH_AT="05:00"' in workflow
    assert 'PUBLISH_AT="08:00"' in workflow
    assert 'PUBLISH_AT="11:00"' in workflow
    assert 'PUBLISH_AT="17:00"' in workflow
    assert 'timeout-minutes: 180' in workflow
    assert 'sleep "${FINAL_WAIT}"' in workflow
    post_command = workflow.split('curl --fail-with-body')[1].split('> story-response.json')[0]
    assert '--retry' not in post_command
    assert '2026-09-08' in workflow
    assert 'wait_until_slot:' in workflow and 'dry_run:' in workflow
    assert "inputs.dry_run != true" in workflow
    assert "steps.published-marker.outputs.cache-hit != 'true'" in workflow
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
