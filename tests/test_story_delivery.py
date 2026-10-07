from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx
from PIL import Image, ImageDraw

from backend.instagram import InstagramPublisher, InstagramPublishUnknown
from backend.story_delivery import inspect_story_image, verify_public_image
import backend.story_automation_four as automation


def jpeg(*, black=False, quality=90):
    image = Image.new("RGB", (1080, 1920), "black" if black else "#faf6ed")
    if not black:
        draw = ImageDraw.Draw(image)
        draw.rectangle((120, 200, 960, 1500), fill="#23475a")
        draw.ellipse((360, 1550, 1020, 1900), fill="#f9d200")
    data = BytesIO()
    image.save(data, format="JPEG", quality=quality)
    return data.getvalue()


class ImageChecks(unittest.TestCase):
    def test_black_and_non_image_responses_are_rejected(self):
        for payload in (jpeg(black=True), b"<html>not an image</html>"):
            with self.assertRaises(RuntimeError):
                inspect_story_image(payload)

    def test_recompressed_instagram_image_matches(self):
        self.assertTrue(inspect_story_image(jpeg(quality=75), expected=jpeg())["matches_render"])

    def test_public_404_is_read_only(self):
        calls = []
        def handler(request):
            calls.append(request.method)
            return httpx.Response(404)
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with patch("backend.story_delivery.time.sleep"), self.assertRaises(RuntimeError):
                verify_public_image("https://example.com/missing.jpg", jpeg(), client=client)
        self.assertEqual(calls, ["GET"] * 3)

    def test_cached_wrong_source_is_rejected(self):
        with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=jpeg(quality=75)))) as client:
            with patch("backend.story_delivery.time.sleep"), self.assertRaises(RuntimeError):
                verify_public_image("https://example.com/story.jpg", jpeg(), client=client)

    def test_public_source_matches_exact_bytes(self):
        source = jpeg()
        with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=source))) as client:
            self.assertTrue(verify_public_image("https://example.com/story.jpg", source, client=client)["matches_render"])


class PublishedChecks(unittest.TestCase):
    def publisher(self, handler):
        return InstagramPublisher(user_id="123", access_token="private-token",
                                  publish_settle_seconds=0,
                                  client=httpx.Client(transport=httpx.MockTransport(handler)))

    def test_id_saved_before_delivery_and_cdn_get_has_no_token(self):
        saved = []
        calls = []
        def handler(request):
            calls.append((request.method, request.url.path))
            if request.url.path.endswith("/123/media"):
                return httpx.Response(200, json={"id": "container"})
            if request.url.path.endswith("/container"):
                return httpx.Response(200, json={"status_code": "FINISHED"})
            if request.url.path.endswith("/123/media_publish"):
                return httpx.Response(200, json={"id": "media"})
            if request.url.path.endswith("/media"):
                self.assertEqual(saved, ["media"])
                return httpx.Response(200, json={"id": "media", "media_url": "https://cdn.example.com/story.jpg"})
            self.assertNotIn("authorization", request.headers)
            return httpx.Response(200, content=jpeg(quality=75))
        publisher = self.publisher(handler)
        self.assertEqual(publisher.publish_story("https://example.com/story.jpg", expected_image=jpeg(),
                                                on_published=saved.append), "media")
        self.assertTrue(publisher.last_delivery_check["passed"])
        self.assertEqual(sum(method == "POST" and path.endswith("media_publish") for method, path in calls), 1)

    def test_black_delivered_image_is_flagged_without_republishing(self):
        methods = []
        def handler(request):
            methods.append(request.method)
            if request.url.path.endswith("/media"):
                return httpx.Response(200, json={"id": "media", "media_url": "https://cdn.example.com/black.jpg"})
            return httpx.Response(200, content=jpeg(black=True))
        publisher = self.publisher(handler)
        with patch("backend.instagram.time.sleep"):
            self.assertFalse(publisher.verify_published("media", expected_image=jpeg()))
        self.assertIn("black or blank", publisher.last_delivery_check["reason"])
        self.assertTrue(all(method == "GET" for method in methods))

    def test_publish_timeout_is_unknown_and_not_retried(self):
        calls = []
        def handler(request):
            calls.append(request.method)
            raise httpx.ReadTimeout("lost response", request=request)
        publisher = self.publisher(handler)
        with self.assertRaises(InstagramPublishUnknown):
            publisher.publish_container("container")
        self.assertEqual(calls, ["POST"])


class AutomationChecks(unittest.TestCase):
    def run_post(self, root, *, source_failure=False, unknown=False):
        class Publisher:
            last_delivery_check = {"passed": False, "reason": "CDN unavailable"}
            def publish_story(self, url, *, expected_image, on_published):
                if unknown:
                    raise InstagramPublishUnknown("unknown publish")
                on_published("media")
                record = json.loads((root / "story_runs/2026-10-09-morning.json").read_text(encoding="utf-8"))
                assert record["status"] == "published" and record["media_id"] == "media"
                return "media"
        source_check = RuntimeError("source HTTP 404") if source_failure else None
        with patch.dict("os.environ", {"PUBLIC_BASE_URL": "https://example.com"}), \
             patch.object(automation, "build_daily_sky", return_value={}), \
             patch.object(automation, "build_slot_content", return_value={}), \
             patch.object(automation, "render_slot_story", side_effect=lambda content, day, path: (path.parent.mkdir(parents=True, exist_ok=True), path.write_bytes(jpeg()))), \
             patch.object(automation, "validate_story_asset", return_value={"passed": True}), \
             patch.object(automation, "verify_public_image", side_effect=source_check, return_value={"passed": True}), \
             patch.object(automation, "_notify_failure"), \
             patch.object(automation, "InstagramPublisher", Publisher):
            return automation.run_story_slot("2026-10-09", generated_root=root)

    def test_source_failure_prevents_instagram_post(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(RuntimeError):
                self.run_post(root, source_failure=True)
            record = json.loads((root / "story_runs/2026-10-09-morning.json").read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "source_failed")
            self.assertFalse(record["publish_request_sent"])

    def test_failed_delivery_keeps_published_id_and_skips_next_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = self.run_post(root)
            self.assertEqual(record["status"], "published")
            self.assertFalse(record["delivery_check"]["passed"])
            self.assertRegex(record["asset_url"], r"morning-[0-9a-f]{32}\.jpg$")
            self.assertTrue(automation.run_story_slot("2026-10-09", generated_root=root)["skipped"])

    def test_unknown_publish_is_blocked_on_next_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(InstagramPublishUnknown):
                self.run_post(root, unknown=True)
            with self.assertRaisesRegex(RuntimeError, "result is unknown"):
                automation.run_story_slot("2026-10-09", generated_root=root)


if __name__ == "__main__":
    unittest.main()
