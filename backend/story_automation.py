from __future__ import annotations

from datetime import date, datetime
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

from .instagram import InstagramPublisher
from .story_copy import DailyStoryCopy, generate_story_copy
from .story_renderer import render_story_images
from .story_sky import build_daily_sky


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GENERATED_ROOT = PROJECT_ROOT / "generated"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _recent_titles(runs_dir: Path) -> list[str]:
    titles: list[str] = []
    for path in sorted(runs_dir.glob("*.json"), reverse=True)[:14]:
        record = _read_json(path) or {}
        for slide in record.get("copy", {}).get("slides", []):
            title = str(slide.get("title", "")).strip()
            if title:
                titles.append(title)
    return titles


def _target_date(value: str | date | None) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    tz = ZoneInfo(os.getenv("STORY_TIMEZONE", "Asia/Tokyo"))
    return datetime.now(tz).date()


def _asset_urls(target: date, count: int) -> list[str]:
    public_base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    encoded_date = quote(target.isoformat(), safe="")
    return [
        f"{public_base_url}/story-assets/{encoded_date}/slide-{index}.jpg"
        for index in range(1, count + 1)
    ]


def _notify_failure(target: date, message: str) -> None:
    webhook_url = os.getenv("ERROR_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return
    try:
        httpx.post(
            webhook_url,
            json={
                "text": f"Instagramストーリー自動投稿に失敗しました（{target.isoformat()}）: {message}",
                "target_date": target.isoformat(),
                "status": "failed",
            },
            timeout=15,
        ).raise_for_status()
    except Exception:
        pass


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
    base_record: dict[str, Any] = {
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
        _write_json(record_path, base_record)
        return base_record

    public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip()
    if not public_base_url.startswith("https://"):
        raise RuntimeError("PUBLIC_BASE_URL には公開HTTPS URLを設定してください。")

    _write_json(record_path, base_record)
    try:
        publisher = InstagramPublisher()
        start_index = len(published_media_ids)
        for index in range(start_index, len(urls)):
            media_id = publisher.publish_story(urls[index])
            published_media_ids.append(media_id)
            base_record["published_media_ids"] = published_media_ids
            base_record["updated_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
            _write_json(record_path, base_record)

        base_record["status"] = "published"
        base_record["completed_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
        base_record["updated_at"] = base_record["completed_at"]
        _write_json(record_path, base_record)
        return base_record
    except Exception as exc:
        base_record["status"] = "failed"
        base_record["error"] = str(exc)[:500]
        base_record["updated_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
        _write_json(record_path, base_record)
        _notify_failure(target, str(exc)[:300])
        raise
