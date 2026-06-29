from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PlaywrightLinkedInPublisher:
    profile_dir: Path
    headless: bool = True
    feed_url: str = "https://www.linkedin.com/feed/"
    timeout_ms: int = 30_000
    playwright_factory: Any | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "PlaywrightLinkedInPublisher":
        profile_dir = str(config.get("profile_dir") or config.get("user_data_dir") or "").strip()
        if not profile_dir:
            raise ValueError("LinkedIn Playwright config must include profile_dir")
        return cls(
            profile_dir=Path(profile_dir),
            headless=bool(config.get("headless", True)),
            feed_url=str(config.get("feed_url") or "https://www.linkedin.com/feed/").strip(),
            timeout_ms=int(config.get("timeout_ms", 30_000)),
        )

    def publish(self, post: str) -> None:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        factory = self.playwright_factory
        if factory is None:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError("Playwright is not installed") from exc

            factory = sync_playwright

        with factory() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=self.headless,
                viewport={"width": 1280, "height": 1400},
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(self.feed_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                self._create_post(page, post)
            finally:
                context.close()

    def _create_post(self, page, post: str) -> None:
        self._click_first(
            page,
            [
                lambda: page.get_by_role("button", name=re.compile(r"start a post|create a post", re.I)),
                lambda: page.locator("button[aria-label*='Start a post']"),
                lambda: page.get_by_text("Start a post", exact=False),
            ],
        )

        composer = page.get_by_role("textbox").first
        composer.wait_for(state="visible", timeout=self.timeout_ms)
        try:
            composer.fill(post, timeout=self.timeout_ms)
        except Exception:
            composer.click(timeout=self.timeout_ms)
            page.keyboard.insert_text(post)

        self._click_first(
            page,
            [
                lambda: page.get_by_role("button", name=re.compile(r"^post$", re.I)),
                lambda: page.locator("button[aria-label='Post']"),
            ],
        )

    def _click_first(self, page, locators: list) -> None:
        last_error: Exception | None = None
        for factory in locators:
            try:
                locator = factory()
                locator.first.click(timeout=self.timeout_ms)
                return
            except Exception as exc:  # pragma: no cover - browser-specific fallback behavior
                last_error = exc
        raise RuntimeError("LinkedIn compose flow could not be completed") from last_error
