from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class ProcessedSubmissionRecord:
    submission_id: str
    title: str
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    github_status: str = "pending"
    github_commit: str | None = None
    linkedin_status: str = "pending"
    linkedin_error: str | None = None
    github_error: str | None = None
