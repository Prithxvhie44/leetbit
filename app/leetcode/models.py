from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Submission:
    id: str
    title: str
    slug: str
    problem_id: str | None
    difficulty: str
    language: str
    code: str
    url: str
