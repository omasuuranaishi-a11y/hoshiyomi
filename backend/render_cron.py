"""Independent Render Cron trigger for the three daily Instagram Stories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import json
import os
import time as time_module
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import httpx


JST = ZoneInfo("Asia/Tokyo")
EARLY_WINDOW = timedelta(minutes=15)
LATE_WINDOW = timedelta(minutes=90)
DAILY_TARGETS = (
    (time(5, 0), "morning"),
    (time(11, 0), "night"),
    (time(17, 0), "evening"),
)


@dataclass(frozen=True)
class RunSpec:
    target_date: date
    slot: str
    publish_at: datetime


def resolve_run(now: datetime | None = None) -> RunSpec:
    current = (now or datetime.now(JST)).astimezone(JST)
    candidates: list[RunSpec] = []
    for day_offset in (-1, 0, 1):
        candidate_date = current.date() + timedelta(days=day_offset)
        for target_time, slot in DAILY_TARGETS:
            publish_at = datetime.combine(candidate_date, target_time, tzinfo=JST)
            delta = current - publish_at
            if -EARLY_WINDOW <= delta <= LATE_WINDOW:
                candidates.append(RunSpec(candidate_date, slot, publish_at))

    if not candidates:
        raise RuntimeError(
            f"No Instagram Story slot is due near {current.isoformat()}; refusing to guess."
        )
    return min(candidates, key=lambda item: abs(current - item.publish_at))


def healthcheck_url(automation_url: str) -> str:
    parsed = urlsplit(automation_url)
    return urlunsplit((parsed.scheme, parsed.netloc, "/healthz", "", ""))


def _warm_service(client: httpx.Client, url: str) -> None:
    for attempt in range(1, 4):
        try:
            response = client.get(healthcheck_url(url), timeout=120)
            response.raise_for_status()
            print(f"Render web service is warm (attempt {attempt}).")
            return
        except httpx.HTTPError as exc:
            print(f"Warm-up attempt {attempt} failed: {type(exc).__name__}")
            if attempt < 3:
                time_module.sleep(5)
    print("Warm-up did not succeed; the publish request will still be attempted once.")


def main() -> None:
    automation_url = os.getenv("AUTOMATION_URL", "").strip()
    secret = os.getenv("RENDER_CRON_SECRET", "").strip()
    if not automation_url.startswith("https://"):
        raise RuntimeError("AUTOMATION_URL must be a public HTTPS URL.")
    if not secret:
        raise RuntimeError("RENDER_CRON_SECRET is not configured.")

    run = resolve_run()
    print(
        f"Resolved {run.target_date.isoformat()}/{run.slot} for "
        f"{run.publish_at.isoformat()}."
    )

    with httpx.Client(follow_redirects=True) as client:
        _warm_service(client, automation_url)
        wait_seconds = (run.publish_at - datetime.now(JST)).total_seconds()
        if wait_seconds > 0:
            print(f"Waiting {wait_seconds:.0f}s for the exact JST target.")
            time_module.sleep(wait_seconds)

        # Do not retry this POST. If its response is ambiguous, the later
        # GitHub watchdog calls the same idempotent API and verifies the record.
        response = client.post(
            automation_url,
            params={"slot": run.slot, "target_date": run.target_date.isoformat()},
            headers={"Authorization": f"Bearer {secret}"},
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
