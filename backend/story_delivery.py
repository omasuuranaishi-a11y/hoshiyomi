"""Check image bytes at the public source and after Instagram processing."""
from __future__ import annotations

import hashlib
from io import BytesIO
import time
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageChops, ImageStat

DELIVERY_VERSION = "2026-10-08-image-check-v1"


def inspect_story_image(payload: bytes, *, expected: bytes | None = None) -> dict:
    if not payload or len(payload) > 8 * 1024 * 1024:
        raise RuntimeError("Image delivery check: invalid image byte count")
    try:
        with Image.open(BytesIO(payload)) as image:
            if image.format != "JPEG":
                raise RuntimeError("Image delivery check: response is not a JPEG")
            image.load()
            width, height = image.size
            if width < 360 or height < 640 or abs(width / height - 9 / 16) > .025:
                raise RuntimeError("Image delivery check: unexpected story dimensions")
            sample = image.convert("RGB").resize((64, 114))
    except (OSError, ValueError) as exc:
        raise RuntimeError("Image delivery check: image cannot be decoded") from exc
    stats = ImageStat.Stat(sample.convert("L"))
    if stats.mean[0] < 5 or stats.stddev[0] < 3:
        raise RuntimeError("Image delivery check: image is black or blank")
    report = {"passed": True, "width": width, "height": height,
              "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
              "luminance": round(stats.mean[0], 2)}
    if expected is not None:
        with Image.open(BytesIO(expected)) as original:
            reference = original.convert("RGB").resize(sample.size)
        difference = sum(ImageStat.Stat(ImageChops.difference(sample, reference)).mean) / 3
        if difference > 20:
            raise RuntimeError("Image delivery check: delivered image differs from the approved render")
        report.update(matches_render=True, mean_pixel_difference=round(difference, 2))
    return report


def verify_public_image(url: str, expected: bytes, *, client: httpx.Client | None = None) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("Image delivery check: public HTTPS URL is required")
    # Only GETs are repeated; no Instagram publishing request is sent here.
    expected_hash = hashlib.sha256(expected).hexdigest()
    for attempt in range(3):
        try:
            get = client.get if client is not None else httpx.get
            response = get(url, headers={"Cache-Control": "no-cache"}, timeout=8,
                           follow_redirects=True)
            if response.status_code != 200:
                raise RuntimeError(f"Image delivery check: source HTTP {response.status_code}")
            report = inspect_story_image(response.content)
            if report["sha256"] != expected_hash:
                raise RuntimeError("Image delivery check: public source bytes do not match the render")
            return {**report, "matches_render": True, "attempts": attempt + 1}
        except httpx.RequestError:
            reason = "Image delivery check: public source could not be fetched"
        except RuntimeError as exc:
            reason = str(exc)
        if attempt < 2:
            time.sleep(1)
    raise RuntimeError(reason)
