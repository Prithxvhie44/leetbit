from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from app.leetcode.models import Submission


def parse_submission(payload: Mapping[str, Any]) -> Submission:
    submission_data = _extract_submission_mapping(payload)
    if submission_data is None:
        raise ValueError("No submission payload found")

    title = str(submission_data.get("title") or payload.get("title") or "Untitled Problem")
    slug = str(submission_data.get("titleSlug") or submission_data.get("slug") or _slugify(title))
    problem_id = _first_present(
        submission_data.get("questionFrontendId"),
        submission_data.get("frontendQuestionId"),
        submission_data.get("questionId"),
        payload.get("questionFrontendId"),
        payload.get("frontendQuestionId"),
        payload.get("questionId"),
    )
    difficulty = str(submission_data.get("difficulty") or payload.get("difficulty") or "Unknown")
    language = str(submission_data.get("lang") or submission_data.get("language") or "Unknown")
    code = str(submission_data.get("code") or submission_data.get("sourceCode") or payload.get("code") or "")
    submission_id = str(submission_data.get("id") or submission_data.get("submissionId") or payload.get("id") or slug)
    url = str(submission_data.get("url") or f"https://leetcode.com/problems/{slug}/")

    return Submission(
        id=submission_id,
        title=title,
        slug=slug,
        problem_id=str(problem_id) if problem_id is not None else None,
        difficulty=difficulty,
        language=language,
        code=code,
        url=url,
    )


def _extract_submission_mapping(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    candidates = (
        payload.get("recentAcSubmissionList"),
        payload.get("recentSubmissionList"),
        payload.get("recentAcSubmission"),
        payload.get("submission"),
    )
    for candidate in candidates:
        if isinstance(candidate, list) and candidate:
            first_item = candidate[0]
            if isinstance(first_item, Mapping):
                return first_item
        if isinstance(candidate, Mapping):
            return candidate
    if isinstance(payload, Mapping) and "data" in payload and isinstance(payload["data"], Mapping):
        return _extract_submission_mapping(payload["data"])
    return None


def _slugify(title: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip().lower())
    return normalized.strip("-") or "untitled-problem"


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None
