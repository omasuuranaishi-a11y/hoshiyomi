from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import urlparse

import httpx


class InstagramAPIError(RuntimeError):
    pass


class InstagramPublisher:
    def __init__(
        self,
        *,
        user_id: str | None = None,
        access_token: str | None = None,
        graph_base_url: str | None = None,
        api_version: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.user_id = user_id or os.getenv("INSTAGRAM_USER_ID", "").strip()
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        self.graph_base_url = (
            graph_base_url
            or os.getenv("INSTAGRAM_GRAPH_BASE_URL", "https://graph.instagram.com")
        ).rstrip("/")
        self.api_version = api_version or os.getenv("INSTAGRAM_API_VERSION", "v25.0")
        self.client = client or httpx.Client(timeout=60, follow_redirects=True)

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
        message = body.get("error", {}).get("message") or body.get("message") or "不明なエラー"
        raise InstagramAPIError(
            f"Instagram APIエラー（HTTP {response.status_code}）: {message}"
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
        response = self.client.post(
            self._url(f"{self.user_id}/media_publish"),
            headers=self._headers,
            data={"creation_id": container_id},
        )
        self._raise_for_error(response)
        media_id = self._body(response).get("id")
        if not media_id:
            raise InstagramAPIError("公開後のInstagramメディアIDを取得できませんでした。")
        return str(media_id)

    def publish_story(self, image_url: str) -> str:
        container_id = self.create_story_container(image_url)
        self.wait_until_ready(container_id)
        return self.publish_container(container_id)
