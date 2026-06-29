from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LinkedInAPIPublisher:
    publish_url: str
    access_token: str | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "LinkedInAPIPublisher":
        publish_url = str(config.get("publish_url") or "").strip()
        if not publish_url:
            raise ValueError("LinkedIn API config must include a publish URL")
        access_token = config.get("access_token")
        return cls(publish_url=publish_url, access_token=str(access_token).strip() if access_token else None)

    def publish(self, post: str) -> None:
        import httpx

        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        response = httpx.post(self.publish_url, json={"post": post}, headers=headers, timeout=30.0)
        response.raise_for_status()
