from __future__ import annotations

import os
import time
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from .story_delivery import inspect_story_image


class InstagramAPIError(RuntimeError):
    pass


class InstagramPublishUnknown(InstagramAPIError):
    """A publishing POST may have completed; never automatically repeat it."""


class InstagramPublisher:
    def __init__(
        self,
        *,
        user_id: str | None = None,
        access_token: str | None = None,
        graph_base_url: str | None = None,
        api_version: str | None = None,
        publish_settle_seconds: float | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.user_id = user_id or os.getenv("INSTAGRAM_USER_ID", "").strip()
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        configured_graph_url = (
            graph_base_url
            or os.getenv("INSTAGRAM_GRAPH_BASE_URL", "https://graph.facebook.com")
        ).rstrip("/")
        # This service uses Facebook Login + a Page access token for a connected
        # Instagram business account. That flow publishes through graph.facebook.com.
        if configured_graph_url == "https://graph.instagram.com":
            configured_graph_url = "https://graph.facebook.com"
        self.graph_base_url = configured_graph_url
        self.api_version = api_version or os.getenv("INSTAGRAM_API_VERSION", "v25.0")
        self.publish_settle_seconds = (
            publish_settle_seconds
            if publish_settle_seconds is not None
            else float(os.getenv("INSTAGRAM_PUBLISH_SETTLE_SECONDS", "5"))
        )
        self.client = client or httpx.Client(timeout=60, follow_redirects=True)
        self.last_delivery_check: dict[str, Any] = {"passed": False, "reason": "not checked"}

        if not self.user_id or not self.access_token:
            raise RuntimeError(
                "INSTAGRAM_USER_ID と INSTAGRAM_ACCESS_TOKEN を設定してください。"
            )

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def _url(self, path: str) -> str:
        return f"{self.graph_base_url}/{self.api_version}/{path.lstrip('/')}"

    @staticmethod
    def _body(response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError as exc:
            raise InstagramAPIError(
                f"Instagram APIからJSON以外の応答が返りました（HTTP {response.status_code}）。"
            ) from exc

    def _raise_for_error(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        body = self._body(response)
        error = body.get("error", {})
        message = error.get("message") or body.get("message") or "不明なエラー"
        details = []
        if error.get("code") is not None:
            details.append(f"code={error['code']}")
        if error.get("error_subcode") is not None:
            details.append(f"subcode={error['error_subcode']}")
        if error.get("fbtrace_id"):
            details.append(f"trace={error['fbtrace_id']}")
        detail_suffix = f" ({', '.join(details)})" if details else ""
        raise InstagramAPIError(
            f"Instagram APIエラー（HTTP {response.status_code}）: {message}{detail_suffix}"
        )

    def create_story_container(self, image_url: str) -> str:
        parsed = urlparse(image_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Instagramへ渡す画像URLは公開HTTPS URLである必要があります。")
        response = self.client.post(
            self._url(f"{self.user_id}/media"),
            headers=self._headers,
            data={"image_url": image_url, "media_type": "STORIES"},
        )
        self._raise_for_error(response)
        container_id = self._body(response).get("id")
        if not container_id:
            raise InstagramAPIError("InstagramのメディアコンテナIDを取得できませんでした。")
        return str(container_id)

    def wait_until_ready(
        self,
        container_id: str,
        *,
        attempts: int = 15,
        interval_seconds: float = 2.0,
    ) -> None:
        last_status = "UNKNOWN"
        for attempt in range(attempts):
            response = self.client.get(
                self._url(container_id),
                headers=self._headers,
                params={"fields": "status_code,status"},
            )
            self._raise_for_error(response)
            body = self._body(response)
            last_status = str(body.get("status_code") or "UNKNOWN").upper()
            if last_status in {"FINISHED", "PUBLISHED"}:
                return
            if last_status in {"ERROR", "EXPIRED"}:
                raise InstagramAPIError(
                    f"Instagramの画像処理に失敗しました（{last_status}）。"
                )
            if attempt < attempts - 1:
                time.sleep(interval_seconds)
        raise InstagramAPIError(
            f"Instagramの画像処理が時間内に完了しませんでした（{last_status}）。"
        )

    def publish_container(self, container_id: str) -> str:
        try:
            response = self.client.post(
                self._url(f"{self.user_id}/media_publish"),
                headers=self._headers,
                data={"creation_id": container_id},
            )
        except httpx.RequestError as exc:
            raise InstagramPublishUnknown("Instagram publish response was lost; do not resend") from exc
        if response.status_code >= 500:
            raise InstagramPublishUnknown("Instagram publish result is unknown; do not resend")
        self._raise_for_error(response)
        try:
            media_id = self._body(response).get("id")
        except InstagramAPIError as exc:
            raise InstagramPublishUnknown("Instagram publish returned an unreadable result; do not resend") from exc
        if not media_id:
            raise InstagramPublishUnknown("公開後のInstagramメディアIDを取得できませんでした。再送しないでください。")
        return str(media_id)

    def verify_published(self, media_id: str, *, attempts: int = 3,
                         expected_image: bytes | None = None) -> bool:
        """Read the delivered image without issuing another publishing POST."""
        last_error = "not visible"
        for attempt in range(attempts):
            try:
                response = self.client.get(
                    self._url(media_id),
                    headers=self._headers,
                    params={"fields": "id,media_type,timestamp,media_url" if expected_image is not None
                            else "id,media_type,timestamp"},
                    timeout=8,
                )
                self._raise_for_error(response)
                body = self._body(response)
                if str(body.get("id")) == str(media_id):
                    report: dict[str, Any] = {"passed": True, "media_id": str(media_id),
                                              "timestamp": body.get("timestamp")}
                    if expected_image is not None:
                        media_url = str(body.get("media_url") or "")
                        if urlparse(media_url).scheme != "https":
                            raise InstagramAPIError("Published image URL is not available yet")
                        # Do not send the Graph access token to the image CDN.
                        image_response = self.client.get(media_url, timeout=8)
                        if image_response.status_code != 200:
                            raise InstagramAPIError(f"Published image HTTP {image_response.status_code}")
                        report["image"] = inspect_story_image(image_response.content, expected=expected_image)
                    self.last_delivery_check = report
                    return True
                last_error = "media id did not match"
            except httpx.RequestError:
                last_error = "Published image confirmation connection failed"
            except (InstagramAPIError, RuntimeError) as exc:
                last_error = str(exc)[:300]
            if attempt < attempts - 1:
                time.sleep(2)
        self.last_delivery_check = {"passed": False, "media_id": str(media_id), "reason": last_error}
        return False

    def publish_story(self, image_url: str, *, expected_image: bytes | None = None,
                      on_published: Callable[[str], None] | None = None) -> str:
        container_id = self.create_story_container(image_url)
        self.wait_until_ready(container_id)
        # Meta can report FINISHED a few seconds before media_publish can resolve
        # the container globally. A short settling delay avoids that transient
        # "Media ID is not available" window without issuing a duplicate POST.
        if self.publish_settle_seconds > 0:
            time.sleep(self.publish_settle_seconds)
        media_id = self.publish_container(container_id)
        # Persist the returned id before any slower, read-only delivery checks.
        if on_published is not None:
            on_published(media_id)
        self.verify_published(media_id, expected_image=expected_image)
        return media_id
