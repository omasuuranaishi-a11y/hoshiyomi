"""Keep the approved GitHub publisher ready before each JST publishing time.

This clock never calls Instagram or Render. It dispatches the existing publisher
once per upcoming date/slot, then hands off to a fresh runner within 180 minutes.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, time as day_time, timedelta, timezone
import json
import os
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

JST = timezone(timedelta(hours=9))
PUBLISHER = "daily-instagram-story.yml"
CLOCK = "instagram-story-clock.yml"
SLOTS = (("morning", 4), ("horoscope", 5), ("evening", 17))
LEAD = timedelta(minutes=15)
MAX_RUNTIME_MINUTES = 170
ACTIVE = {"queued", "in_progress", "waiting", "pending", "requested"}


def log(message: str) -> None:
    print(f"{datetime.now(JST).isoformat(timespec='seconds')} {message}", flush=True)


def upcoming_slots(now: datetime, start_date: date):
    """Only current/future slots; never backfill an elapsed publishing time."""
    local = now.astimezone(JST)
    for offset in range(2):
        target = local.date() + timedelta(days=offset)
        if target < start_date:
            continue
        for slot, hour in SLOTS:
            due = datetime.combine(target, day_time(hour), JST)
            if local < due:
                yield target, slot, due


def publication_inputs(target: date, slot: str, request_id: str, *, preview=False):
    if slot not in {name for name, _ in SLOTS}:
        raise ValueError("Unsupported story slot")
    return {
        "slot": slot,
        "target_date": target.isoformat(),
        "wait_until_slot": "false" if preview else "true",
        "dry_run": "true" if preview else "false",
        "force_repost": "false",
        "mark_published_only": "false",
        "clock_request_id": request_id,
    }


class GitHub:
    def __init__(self):
        self.repo = os.environ["GITHUB_REPOSITORY"]
        self.token = os.environ["GH_TOKEN"]
        self.base = os.environ.get("GITHUB_API_URL", "https://api.github.com")

    def request(self, path: str, payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(
            f"{self.base}/repos/{self.repo}/{path}",
            data=body,
            method="GET" if payload is None else "POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        # No retry for any POST. Unknown dispatch outcomes must not be resent.
        try:
            with urlopen(req, timeout=30) as response:
                raw = response.read()
        except HTTPError as exc:
            raise RuntimeError(f"GitHub API {req.method} returned HTTP {exc.code}") from None
        return json.loads(raw) if raw else {}

    def dispatch(self, workflow: str, inputs: dict):
        return self.request(f"actions/workflows/{workflow}/dispatches", {
            "ref": "main", "inputs": inputs,
        })

    def runs(self, workflow: str, **filters):
        query = urlencode({"branch": "main", "per_page": 100, **filters})
        return self.request(f"actions/workflows/{workflow}/runs?{query}")["workflow_runs"]

    def published(self, target: date, slot: str) -> bool:
        internal = "noon" if slot == "horoscope" else slot
        key = f"instagram-story-{target.isoformat()}-{internal}"
        query = urlencode({"key": key, "ref": "refs/heads/main", "per_page": 100})
        return any(item["key"] == key for item in self.request(
            f"actions/caches?{query}"
        )["actions_caches"])

    def prepare_once(self, target: date, slot: str) -> bool:
        """Return False only while another publisher is active; otherwise done."""
        ticket = f"{target.isoformat()}-{slot}"
        if self.published(target, slot):
            log(f"Already published: {ticket}")
            return True
        runs = self.runs(PUBLISHER)
        if any(run.get("display_title") == f"clock-{ticket}" for run in runs):
            log(f"Already requested (no resend): {ticket}")
            return True
        if any(run["status"] in ACTIVE for run in runs):
            log(f"Publisher active; checking again before {ticket}")
            return False
        # A failed or timed-out POST propagates and ends this clock. We never
        # retry publication dispatches when the result may be unknown.
        self.dispatch(PUBLISHER, publication_inputs(target, slot, ticket))
        log(f"Prepared {ticket}; publisher will wait for its approved JST time")
        return True


def run_clock(api: GitHub, start_date: date, runtime_minutes: int):
    if not 1 <= runtime_minutes <= MAX_RUNTIME_MINUTES:
        raise ValueError("Clock runtime must be within 1..170 minutes")
    deadline = time.monotonic() + runtime_minutes * 60
    handled = set()
    next_heartbeat = 0.0
    log(f"Clock ready; first eligible date={start_date}; runtime={runtime_minutes}m")
    while time.monotonic() < deadline:
        now = datetime.now(JST)
        for target, slot, due in upcoming_slots(now, start_date):
            ticket = (target, slot)
            if ticket not in handled and due - LEAD <= now < due:
                if api.prepare_once(target, slot):
                    handled.add(ticket)
        if time.monotonic() >= next_heartbeat:
            log("Clock healthy; times=04:00,05:00,17:00 JST; no past-slot dispatches")
            next_heartbeat = time.monotonic() + 300
        time.sleep(min(20, max(0, deadline - time.monotonic())))
    log("Clock interval complete; handing off to next runner")


def verify(api: GitHub, target: date):
    """Exercise the real dispatch path using previews, then a short handoff."""
    log(f"Cache API verified; preview-date morning marker={api.published(target, 'morning')}")
    tickets = []
    for slot, _ in SLOTS:
        ticket = f"verify-{target}-{slot}-{os.environ['GITHUB_RUN_ID']}"
        api.dispatch(PUBLISHER, publication_inputs(target, slot, ticket, preview=True))
        tickets.append(f"clock-{ticket}")
        log(f"Preview requested (never publish): {slot}/{target}")
        # Global publisher concurrency has one pending slot. Wait for each
        # preview before dispatching the next, so none can replace another.
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            found = next((r for r in api.runs(PUBLISHER, event="workflow_dispatch")
                          if r.get("display_title") == tickets[-1]), None)
            if found and found["status"] == "completed":
                if found["conclusion"] != "success":
                    raise RuntimeError(f"Preview failed: {slot}; run={found['id']}")
                log(f"Preview passed: {slot}; run={found['id']}")
                break
            time.sleep(5)
        else:
            raise RuntimeError(f"Preview completion unknown: {slot}; no resend")
    api.dispatch(CLOCK, {"mode": "handoff-check"})
    log("Verification handoff dispatched; successor must finish without publishing")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("live", "handoff", "verify", "handoff-check"))
    parser.add_argument("--start-date", type=date.fromisoformat, default=date(2026, 10, 7))
    parser.add_argument("--target-date", type=date.fromisoformat)
    parser.add_argument("--runtime-minutes", type=int, default=MAX_RUNTIME_MINUTES)
    args = parser.parse_args()
    if args.mode == "handoff-check":
        log("Handoff verified: GitHub token started this successor; no posting")
        return
    api = GitHub()
    if args.mode == "live":
        run_clock(api, args.start_date, args.runtime_minutes)
    elif args.mode == "handoff":
        api.dispatch(CLOCK, {"mode": "live"})
        log("Next live clock dispatched; no cron wake-up required")
    else:
        verify(api, args.target_date or datetime.now(JST).date() + timedelta(days=1))


if __name__ == "__main__":
    main()

