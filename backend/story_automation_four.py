from __future__ import annotations
from datetime import date,datetime,timezone
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote
from .instagram import InstagramPublisher
from .story_automation import DEFAULT_GENERATED_ROOT,_notify_failure,_read_json,_target_date,_write_json
from .story_four import SLOTS,build_slot_content,render_slot_story
from .story_quality import design_variant,validate_story_asset
from .story_sky_daily import build_daily_sky

def run_story_slot(target_date:str|date|None=None,*,slot:str="morning",dry_run:bool=False,force:bool=False,generated_root:str|Path|None=None)->dict[str,Any]:
    if slot not in SLOTS:
        raise ValueError("slot must be morning, noon, evening, or night")
    target=_target_date(target_date)
    generated=Path(generated_root or DEFAULT_GENERATED_ROOT)
    record_path=generated/"story_runs"/f"{target.isoformat()}-{slot}.json"
    old=_read_json(record_path)
    if old and old.get("status")=="published" and not force and not dry_run:
        return {**old,"skipped":True,"reason":"already_published"}

    hour={"morning":6,"noon":12,"evening":18,"night":9}[slot]
    facts=build_daily_sky(target,reading_hour=hour)
    content=build_slot_content(facts,slot)
    content["design_variant"]=design_variant(target,slot)["name"]
    name=f"{slot}.jpg"
    path=generated/"story_assets"/target.isoformat()/name
    base=os.getenv("PUBLIC_BASE_URL","http://localhost:8000").rstrip("/")
    url=f"{base}/story-assets/{quote(target.isoformat(),safe='')}/{name}"

    try:
        render_slot_story(content,target,path)
        quality_check=validate_story_asset(path,content,target)
    except Exception as exc:
        failed={
            "target_date":target.isoformat(),
            "slot":slot,
            "status":"quality_failed",
            "facts":facts,
            "content":content,
            "asset_file":str(path),
            "asset_url":url,
            "error":str(exc)[:500],
            "updated_at":datetime.now(timezone.utc).isoformat(),
        }
        _write_json(record_path,failed)
        _notify_failure(target,f"{slot} preflight: {str(exc)[:300]}")
        raise

    record={
        "target_date":target.isoformat(),
        "slot":slot,
        "status":"dry_run" if dry_run else "publishing",
        "facts":facts,
        "content":content,
        "asset_file":str(path),
        "asset_url":url,
        "quality_check":quality_check,
        "updated_at":datetime.now(timezone.utc).isoformat(),
    }
    if dry_run:
        _write_json(record_path,record)
        return record
    if not base.startswith("https://"):
        raise RuntimeError("PUBLIC_BASE_URL must be a public HTTPS URL")
    _write_json(record_path,record)
    try:
        media_id=InstagramPublisher().publish_story(url)
        record.update(status="published",media_id=media_id,completed_at=datetime.now(timezone.utc).isoformat())
        record["updated_at"]=record["completed_at"]
        _write_json(record_path,record)
        return record
    except Exception as exc:
        record.update(status="failed",error=str(exc)[:500],updated_at=datetime.now(timezone.utc).isoformat())
        _write_json(record_path,record)
        _notify_failure(target,f"{slot}: {str(exc)[:300]}")
        raise
