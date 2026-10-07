from __future__ import annotations
from datetime import date,datetime,timezone
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4
from .instagram import InstagramPublisher,InstagramPublishUnknown
from .story_delivery import DELIVERY_VERSION,verify_public_image
from .story_automation import DEFAULT_GENERATED_ROOT,_notify_failure,_read_json,_target_date,_write_json
from .story_four import SLOTS,build_slot_content,render_slot_story
from .story_quality import design_variant,validate_story_asset
from .story_sky_daily import build_daily_sky

def run_story_slot(target_date:str|date|None=None,*,slot:str="morning",dry_run:bool=False,force:bool=False,check_source:bool=False,generated_root:str|Path|None=None)->dict[str,Any]:
    if slot not in SLOTS:
        raise ValueError("slot must be morning, noon, evening, or night")
    target=_target_date(target_date)
    generated=Path(generated_root or DEFAULT_GENERATED_ROOT)
    record_suffix="-preview" if dry_run else ""
    record_path=generated/"story_runs"/f"{target.isoformat()}-{slot}{record_suffix}.json"
    old=_read_json(record_path)
    if old and old.get("status")=="published" and not force and not dry_run:
        return {**old,"skipped":True,"reason":"already_published"}
    if old and old.get("status") in {"publishing","publication_unknown"} and not force and not dry_run:
        raise RuntimeError("Existing publication result is unknown; automatic resend is blocked. Check Instagram before any recovery.")

    hour={"morning":4,"noon":5,"evening":17,"night":11}[slot]
    facts=build_daily_sky(target,reading_hour=hour)
    content=build_slot_content(facts,slot)
    content["design_variant"]=design_variant(target,slot)["name"]
    name=f"{'preview-' if dry_run else ''}{slot}.jpg"
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
        "delivery_version":DELIVERY_VERSION,
        "updated_at":datetime.now(timezone.utc).isoformat(),
    }
    if dry_run and not check_source:
        _write_json(record_path,record)
        return record
    if not base.startswith("https://"):
        raise RuntimeError("PUBLIC_BASE_URL must be a public HTTPS URL")
    # Each attempt uses immutable bytes at a fresh URL; the canonical image
    # remains available for preview and inspection.
    payload=path.read_bytes()
    name=f"{'preview-' if dry_run else ''}{slot}-{uuid4().hex}.jpg"
    path=path.with_name(name)
    path.write_bytes(payload)
    url=f"{base}/story-assets/{quote(target.isoformat(),safe='')}/{name}"
    record.update(asset_file=str(path),asset_url=url)
    try:
        record["source_image_check"]=verify_public_image(url,payload)
    except Exception as exc:
        record.update(status="source_failed",error=str(exc)[:500],
                      publish_request_sent=False,updated_at=datetime.now(timezone.utc).isoformat())
        _write_json(record_path,record)
        _notify_failure(target,f"{slot} source image: {str(exc)[:300]}; no publish request was sent")
        raise
    _write_json(record_path,record)
    if dry_run:
        return record
    def remember_published(media_id:str)->None:
        record.update(status="published",media_id=media_id,completed_at=datetime.now(timezone.utc).isoformat())
        record["updated_at"]=record["completed_at"]
        _write_json(record_path,record)
    try:
        publisher=InstagramPublisher()
        media_id=publisher.publish_story(url,expected_image=payload,on_published=remember_published)
        record["delivery_check"]=publisher.last_delivery_check
        _write_json(record_path,record)
        if not record["delivery_check"].get("passed"):
            _notify_failure(target,f"{slot} published id={media_id}, but image delivery is not confirmed; do not resend")
        return record
    except Exception as exc:
        # Do not label a known published id or an ambiguous publish as unposted.
        status="published" if record.get("media_id") else "publication_unknown" if isinstance(exc,InstagramPublishUnknown) else "failed"
        record.update(status=status,error=str(exc)[:500],updated_at=datetime.now(timezone.utc).isoformat())
        _write_json(record_path,record)
        _notify_failure(target,f"{slot}: {str(exc)[:300]}")
        raise
