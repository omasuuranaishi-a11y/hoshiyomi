from datetime import date, datetime, timedelta, timezone
import unittest
from unittest.mock import patch
from scripts import instagram_story_clock as clock


class ClockTests(unittest.TestCase):
    def test_start_date_and_no_elapsed_slot_backfill(self):
        now = datetime(2026, 10, 6, 17, 30, tzinfo=clock.JST)
        slots = list(clock.upcoming_slots(now, date(2026, 10, 7)))
        self.assertEqual([(slot, due.hour) for _, slot, due in slots],
                         [("morning", 4), ("horoscope", 5), ("evening", 17)])
        self.assertTrue(all(target == date(2026, 10, 7) for target, _, _ in slots))

    def test_jst_midnight_and_utc_conversion(self):
        now = datetime(2026, 10, 6, 19, 0, tzinfo=timezone.utc)
        slots = list(clock.upcoming_slots(now, date(2026, 10, 7)))
        self.assertEqual(slots[0][1], "horoscope")
        self.assertEqual(slots[0][2], datetime(2026, 10, 7, 5, tzinfo=clock.JST))
        self.assertTrue(all(due > now for _, _, due in slots))

    def api(self, *, published=False, runs=(), dispatch_error=None):
        api = object.__new__(clock.GitHub)
        api.published = lambda *args: published
        api.runs = lambda *args, **kwargs: list(runs)
        api.calls = []
        def dispatch(*args):
            api.calls.append(args)
            if dispatch_error:
                raise dispatch_error
        api.dispatch = dispatch
        return api

    def test_marker_prevents_dispatch(self):
        api = self.api(published=True)
        self.assertTrue(api.prepare_once(date(2026, 10, 7), "morning"))
        self.assertEqual(api.calls, [])

    def test_any_active_publisher_prevents_dispatch(self):
        for status in clock.ACTIVE:
            api = self.api(runs=[{"display_title": "another job", "status": status}])
            self.assertFalse(api.prepare_once(date(2026, 10, 7), "horoscope"))
            self.assertEqual(api.calls, [])

    def test_existing_failed_or_unknown_request_never_resends(self):
        for status in ("completed", "in_progress"):
            api = self.api(runs=[{"display_title": "clock-2026-10-07-evening",
                                 "status": status, "conclusion": "failure"}])
            self.assertTrue(api.prepare_once(date(2026, 10, 7), "evening"))
            self.assertEqual(api.calls, [])

    def test_future_dispatch_waits_and_never_forces(self):
        api = self.api()
        self.assertTrue(api.prepare_once(date(2026, 10, 7), "horoscope"))
        workflow, inputs = api.calls[0]
        self.assertEqual(workflow, clock.PUBLISHER)
        self.assertEqual(inputs["target_date"], "2026-10-07")
        self.assertEqual(inputs["slot"], "horoscope")
        self.assertEqual(inputs["wait_until_slot"], "true")
        self.assertEqual(inputs["force_repost"], "false")
        self.assertEqual(inputs["dry_run"], "false")

    def test_unknown_dispatch_outcome_ends_clock_without_retry(self):
        api = self.api(dispatch_error=TimeoutError("unknown outcome"))
        with self.assertRaises(TimeoutError):
            api.prepare_once(date(2026, 10, 7), "morning")
        self.assertEqual(len(api.calls), 1)

    def test_preview_never_publishes_or_waits(self):
        inputs = clock.publication_inputs(date(2026, 10, 7), "evening", "verify", preview=True)
        self.assertEqual(inputs["dry_run"], "true")
        self.assertEqual(inputs["wait_until_slot"], "false")
        self.assertEqual(inputs["force_repost"], "false")

    def test_runtime_guard_preserves_180_minute_limit(self):
        with self.assertRaises(ValueError):
            clock.run_clock(self.api(), date(2026, 10, 7), 180)

    def test_clock_only_dispatches_in_lead_window(self):
        origin = datetime(2026, 10, 7, 3, 44, 40, tzinfo=clock.JST)
        ticks = [0.0]
        class FakeDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return origin + timedelta(seconds=ticks[0])
        api = self.api()
        def sleep(seconds):
            ticks[0] += seconds
        with patch.object(clock, "datetime", FakeDatetime), \
             patch.object(clock.time, "monotonic", lambda: ticks[0]), \
             patch.object(clock.time, "sleep", sleep):
            clock.run_clock(api, date(2026, 10, 7), 1)
        self.assertEqual(len(api.calls), 1)
        self.assertEqual(api.calls[0][1]["slot"], "morning")


if __name__ == "__main__":
    unittest.main()

