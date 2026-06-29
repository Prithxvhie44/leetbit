from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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


@dataclass(slots=True)
class ConnectedAccountRecord:
    provider: str
    data: dict[str, Any]
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def as_json(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "data": self.data,
            "updated_at": self.updated_at.astimezone(timezone.utc).isoformat(),
        }
