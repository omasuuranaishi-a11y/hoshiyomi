from __future__ import annotations

import os
from pathlib import Path
import re
import secrets
from typing import Annotated

from fastapi import Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from .main import app
from .story_automation_final import run_daily_story


ROOT = Path(__file__).resolve().parents[1]


@app.get("/story-assets/{target_date}/{filename}", response_class=FileResponse)
def story_asset(target_date: str, filename: str) -> FileResponse:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", target_date):
        raise HTTPException(status_code=404, detail="not found")
    if not re.fullmatch(r"slide-[1-3]\.jpg", filename):
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
    dry_run: bool = False,
    offline: bool = False,
    force: bool = False,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> JSONResponse:
    expected = os.getenv("AUTOMATION_SECRET", "")
    received = (authorization or "").removeprefix("Bearer ").strip()
    if not expected or not received or not secrets.compare_digest(expected, received):
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        result = run_daily_story(
            target_date,
            dry_run=dry_run,
            offline=offline,
            force=force,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日付の形式を確認してください。") from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="ストーリー自動投稿に失敗しました。") from exc
    return JSONResponse(result)
