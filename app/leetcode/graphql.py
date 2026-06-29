from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx


class LeetCodeGraphQLClient:
    endpoint = "https://leetcode.com/graphql"

    def __init__(
        self,
        username: str,
        session_cookie: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.username = username
        self.session_cookie = session_cookie
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def fetch_recent_accepted_submission(self) -> Mapping[str, Any] | None:
        payload = {
            "query": """
                query recentAcceptedSubmission($username: String!) {
                  recentAcSubmissionList(username: $username, limit: 1) {
                    id
                    title
                    titleSlug
                    questionFrontendId
                    lang
                    code
                    statusDisplay
                    timestamp
                  }
                }
            """,
            "variables": {"username": self.username},
        }
        data = self._post(payload)
        submissions = data.get("recentAcSubmissionList") or []
        if not submissions:
            return None
        submission = dict(submissions[0])
        title_slug = str(submission.get("titleSlug") or submission.get("slug") or "").strip()
        if title_slug:
            submission.update(self.fetch_problem_details(title_slug))
        return submission

    def fetch_problem_details(self, title_slug: str) -> Mapping[str, Any]:
        payload = {
            "query": """
                query questionDetails($titleSlug: String!) {
                  question(titleSlug: $titleSlug) {
                    title
                    titleSlug
                    questionFrontendId
                    difficulty
                    topicTags {
                      name
                      slug
                    }
                  }
                }
            """,
            "variables": {"titleSlug": title_slug},
        }
        data = self._post(payload)
        question = data.get("question") or {}
        if not isinstance(question, dict):
            return {}
        return {
            "title": question.get("title"),
            "titleSlug": question.get("titleSlug"),
            "questionFrontendId": question.get("questionFrontendId"),
            "difficulty": question.get("difficulty"),
            "topicTags": question.get("topicTags") or [],
        }

    def _post(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        response = self._client.post(self.endpoint, json=payload, headers=self._headers())
        response.raise_for_status()
        body = response.json()
        if isinstance(body, dict) and body.get("errors"):
            message = body["errors"][0].get("message") if body["errors"] else "Unknown LeetCode GraphQL error"
            raise RuntimeError(str(message))
        data = body.get("data", {}) if isinstance(body, dict) else {}
        if not isinstance(data, dict):
            return {}
        return data

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": "Leetbit/0.1"}
        if self.session_cookie:
            headers["Cookie"] = f"LEETCODE_SESSION={self.session_cookie}"
        return headers

    def close(self) -> None:
        self._client.close()
