from __future__ import annotations

from app.leetcode.graphql import LeetCodeGraphQLClient
from app.leetcode.models import Submission
from app.leetcode.parser import parse_submission


class LeetCodeDetector:
    def __init__(self, client: LeetCodeGraphQLClient | None) -> None:
        self.client = client

    def detect_latest_accepted_submission(self) -> Submission | None:
        if self.client is None:
            return None
        payload = self.client.fetch_recent_accepted_submission()
        if payload is None:
            return None
        status = str(payload.get("statusDisplay") or "").lower()
        if status and status != "accepted":
            return None
        return parse_submission(payload)
