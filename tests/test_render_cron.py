from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from backend.render_cron import healthcheck_url, resolve_run


JST = ZoneInfo("Asia/Tokyo")


@pytest.mark.parametrize(
    ("now", "slot", "target_date"),
    [
        (datetime(2026, 8, 31, 4, 56, tzinfo=JST), "morning", "2026-08-31"),
        (datetime(2026, 8, 31, 5, 25, tzinfo=JST), "morning", "2026-08-31"),
        (datetime(2026, 8, 31, 10, 56, tzinfo=JST), "night", "2026-08-31"),
        (datetime(2026, 8, 31, 16, 56, tzinfo=JST), "evening", "2026-08-31"),
    ],
)
def test_resolve_run(now, slot, target_date):
    run = resolve_run(now)
    assert run.slot == slot
    assert run.target_date.isoformat() == target_date


def test_resolve_run_refuses_to_guess_far_from_schedule():
    with pytest.raises(RuntimeError, match="refusing to guess"):
        resolve_run(datetime(2026, 8, 31, 9, 0, tzinfo=JST))


def test_healthcheck_url_uses_service_origin():
    assert healthcheck_url(
        "https://example.onrender.com/api/automation/daily-story?unused=true"
    ) == "https://example.onrender.com/healthz"
