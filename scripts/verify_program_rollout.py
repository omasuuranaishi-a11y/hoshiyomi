from datetime import date,timedelta
from pathlib import Path
import json
from PIL import Image,ImageDraw
from backend.story_four import build_slot_content,render_slot_story
from backend.story_sky_daily import build_daily_sky
from backend.story_quality import validate_story_asset

out=Path('generated/program-verification');out.mkdir(parents=True,exist_ok=True)
records=[];errors=[];images=[]
for slot,count,start in [('evening',14,date(2026,9,7)),('noon',32,date(2026,9,8)),('night',14,date(2026,9,7)),('morning',32,date(2026,9,8))]:
    for i in range(count):
        day=start+timedelta(days=i)
        try:
            facts=build_daily_sky(day,reading_hour={'morning':5,'noon':8,'night':11,'evening':17}[slot])
            content=build_slot_content(facts,slot)
            asset=render_slot_story(content,day,out/f'{day}-{slot}.jpg')
            report=validate_story_asset(asset,content,day)
            records.append({'date':str(day),'slot':slot,'headline':content.get('headline',content['title']),'report':report})
            if slot=='evening':images.append(asset)
        except Exception as exc:
            errors.append({'date':str(day),'slot':slot,'error':str(exc)})
if images:
    sheet=Image.new('RGB',(7*270,2*480),'#dddddd')
    for i,p in enumerate(images):
        thumb=Image.open(p).resize((270,480));sheet.paste(thumb,((i%7)*270,(i//7)*480))
    sheet.save(out/'dictionary-overview.jpg',quality=95)
result={'passed':not errors,'rendered':len(records),'errors':errors,'records':records}
(out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':not errors,'rendered':len(records),'errors':errors},ensure_ascii=False))
raise SystemExit(bool(errors))
