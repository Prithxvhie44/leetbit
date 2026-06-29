from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol


class LinkedInPublisher(Protocol):
    def publish(self, post: str) -> None:  # pragma: no cover - protocol method
        raise NotImplementedError


@dataclass(slots=True)
class DisabledLinkedInPublisher:
    def publish(self, post: str) -> None:
        raise RuntimeError("LinkedIn publishing is not configured")


def build_linkedin_publisher(config: str | None) -> LinkedInPublisher | None:
    if not config:
        return None

    parsed = _parse_config(config)
    provider = str(parsed.get("provider") or parsed.get("type") or "").lower().strip()

    if not provider and config.lower().strip() == "disabled":
        return DisabledLinkedInPublisher()

    if provider == "api" or config.lower().startswith("api:"):
        from app.linkedin.api import LinkedInAPIPublisher

        return LinkedInAPIPublisher.from_config(parsed)

    if provider in {"playwright", "browser"} or config.lower().startswith("playwright:"):
        from app.linkedin.playwright import PlaywrightLinkedInPublisher

        return PlaywrightLinkedInPublisher.from_config(parsed)

    return DisabledLinkedInPublisher()


def _parse_config(config: str) -> dict[str, Any]:
    stripped = config.strip()
    if stripped.startswith("{"):
        parsed = json.loads(stripped)
        if not isinstance(parsed, dict):
            raise ValueError("LINKEDIN_CONFIG JSON must be an object")
        return parsed

    if ":" in stripped:
        provider, _, value = stripped.partition(":")
        provider = provider.strip().lower()
        value = value.strip()
        if provider == "playwright":
            return {"provider": "playwright", "profile_dir": value}
        if provider == "api":
            return {"provider": "api", "publish_url": value}

    return {"provider": stripped}
