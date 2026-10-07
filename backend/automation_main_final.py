from __future__ import annotations

import logging
import os
from pathlib import Path
import re
import secrets
from typing import Annotated

from fastapi import Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from .main import app
from .story_automation_four import run_story_slot


ROOT = Path(__file__).resolve().parents[1]


@app.get("/api/automation/story-version")
def story_version():
    from .story_program import (
        HOROSCOPE_COPY_START,
        HOROSCOPE_COPY_VERSION,
        START,
        VERSION,
        editorial_stock,
    )
    from .story_delivery import DELIVERY_VERSION
    return {"version": VERSION, "effective_from_jst": START.isoformat(),
            "delivery_version": DELIVERY_VERSION,
            "horoscope_copy_version": HOROSCOPE_COPY_VERSION,
            "horoscope_effective_from_jst": HOROSCOPE_COPY_START.isoformat(),
            "editorial_stock": editorial_stock()}


@app.get("/story-assets/{target_date}/{filename}", response_class=FileResponse)
def story_asset(target_date: str, filename: str) -> FileResponse:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", target_date):
        raise HTTPException(status_code=404, detail="not found")
    if not re.fullmatch(r"(?:preview-)?(?:morning|noon|evening|night)(?:-[0-9a-f]{32})?\.jpg", filename):
        raise HTTPException(status_code=404, detail="not found")
    asset = ROOT / "generated" / "story_assets" / target_date / filename
    if not asset.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(
        asset,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.post("/api/automation/daily-story")
def daily_story_automation(
    target_date: str | None = None,
    slot: str = "morning",
    dry_run: bool = False,
    force: bool = False,
    verify_media_id: str | None = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> JSONResponse:
    expected = os.getenv("AUTOMATION_SECRET", "")
    received = (authorization or "").removeprefix("Bearer ").strip()
    if not expected or not received or not secrets.compare_digest(expected, received):
        raise HTTPException(status_code=401, detail="unauthorized")
    if verify_media_id and (not dry_run or not re.fullmatch(r"\d{5,30}",verify_media_id)):
        raise HTTPException(status_code=400, detail="Media verification requires preview mode and a numeric media id")
    try:
        result = run_story_slot(
            target_date,
            slot=slot,
            dry_run=dry_run,
            force=force,
            check_source=bool(verify_media_id),
        )
        if verify_media_id:
            from .instagram import InstagramPublisher
            publisher=InstagramPublisher()
            publisher.verify_published(verify_media_id,expected_image=Path(result["asset_file"]).read_bytes())
            result["delivery_check"]=publisher.last_delivery_check
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日付の形式を確認してください。") from exc
    except Exception as exc:
        logging.exception("Daily Story automation failed")
        raise HTTPException(status_code=503, detail=f"{type(exc).__name__}: {str(exc)[:300]}") from exc
    return JSONResponse(result)
