from __future__ import annotations

from datetime import date, datetime
import os
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .instagram import InstagramPublisher
from .story_automation import (
    DEFAULT_GENERATED_ROOT,
    _asset_urls,
    _notify_failure,
    _read_json,
    _recent_titles,
    _target_date,
    _write_json,
)
from .story_copy import DailyStoryCopy, generate_story_copy
from .story_renderer_final import render_story_images
from .story_sky_daily import build_daily_sky


def run_daily_story(
    target_date: str | date | None = None,
    *,
    dry_run: bool = False,
    offline: bool = False,
    force: bool = False,
    generated_root: str | Path | None = None,
) -> dict[str, Any]:
    target = _target_date(target_date)
    generated = Path(generated_root or DEFAULT_GENERATED_ROOT)
    runs_dir = generated / "story_runs"
    record_path = runs_dir / f"{target.isoformat()}.json"
    existing = _read_json(record_path)

    if existing and existing.get("status") == "published" and not force and not dry_run:
        return {**existing, "skipped": True, "reason": "already_published"}

    if existing and existing.get("copy") and not force:
        facts = existing["facts"]
        copy = DailyStoryCopy.model_validate(existing["copy"])
        published_media_ids = list(existing.get("published_media_ids", []))
    else:
        facts = build_daily_sky(target)
        copy = generate_story_copy(
            facts,
            recent_titles=_recent_titles(runs_dir),
            offline=offline,
        )
        published_media_ids = []

    paths = render_story_images(
        copy,
        target,
        output_root=generated / "story_assets",
    )
    urls = _asset_urls(target, len(paths))
    record: dict[str, Any] = {
        "target_date": target.isoformat(),
        "status": "dry_run" if dry_run else "publishing",
        "facts": facts,
        "copy": copy.model_dump(),
        "asset_files": [str(path) for path in paths],
        "asset_urls": urls,
        "published_media_ids": published_media_ids,
        "updated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
    }

    if dry_run:
        _write_json(record_path, record)
        return record

    public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip()
    if not public_base_url.startswith("https://"):
        raise RuntimeError("PUBLIC_BASE_URL には公開HTTPS URLを設定してください。")

    _write_json(record_path, record)
    try:
        publisher = InstagramPublisher()
        for index in range(len(published_media_ids), len(urls)):
            media_id = publisher.publish_story(urls[index])
            published_media_ids.append(media_id)
            record["published_media_ids"] = published_media_ids
            record["updated_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
            _write_json(record_path, record)

        record["status"] = "published"
        record["completed_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
        record["updated_at"] = record["completed_at"]
        _write_json(record_path, record)
        return record
    except Exception as exc:
        record["status"] = "failed"
        record["error"] = str(exc)[:500]
        record["updated_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
        _write_json(record_path, record)
        _notify_failure(target, str(exc)[:300])
        raise
