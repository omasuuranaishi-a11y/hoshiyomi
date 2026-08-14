from __future__ import annotations

import httpx
from unittest.mock import patch

from backend.instagram import InstagramAPIError, InstagramPublisher


def test_publish_story_waits_after_container_is_ready() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if request.url.path.endswith("/123/media"):
            return httpx.Response(200, json={"id": "container-1"})
        if request.url.path.endswith("/container-1"):
            return httpx.Response(200, json={"status_code": "FINISHED"})
        if request.url.path.endswith("/123/media_publish"):
            return httpx.Response(200, json={"id": "media-1"})
        if request.url.path.endswith("/media-1"):
            return httpx.Response(200, json={"id": "media-1", "media_type": "STORY"})
        raise AssertionError(f"Unexpected request: {request.url}")

    sleeps: list[float] = []
    client = httpx.Client(transport=httpx.MockTransport(handler))
    publisher = InstagramPublisher(
        user_id="123",
        access_token="token",
        client=client,
        publish_settle_seconds=5,
    )

    with patch("backend.instagram.time.sleep", side_effect=sleeps.append):
        assert publisher.publish_story("https://example.com/story.jpg") == "media-1"
    assert sleeps == [5]
    assert requests == [
        "/v25.0/123/media",
        "/v25.0/container-1",
        "/v25.0/123/media_publish",
        "/v25.0/media-1",
    ]


def test_api_error_includes_meta_diagnostic_codes() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                400,
                json={
                    "error": {
                        "message": "Media ID is not available",
                        "code": 9007,
                        "error_subcode": 2207027,
                        "fbtrace_id": "trace-123",
                    }
                },
            )
        )
    )
    publisher = InstagramPublisher(
        user_id="123",
        access_token="token",
        client=client,
        publish_settle_seconds=0,
    )

    try:
        publisher.create_story_container("https://example.com/story.jpg")
    except InstagramAPIError as exc:
        assert str(exc).endswith(
            "Media ID is not available (code=9007, subcode=2207027, trace=trace-123)"
        )
    else:
        raise AssertionError("Expected InstagramAPIError")


if __name__ == "__main__":
    test_publish_story_waits_after_container_is_ready()
    test_api_error_includes_meta_diagnostic_codes()
