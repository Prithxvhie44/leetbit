from __future__ import annotations

import time
from dataclasses import dataclass
from logging import Logger, getLogger
from typing import Callable, TypeVar

from app.ai.generator import AIContentGenerator
from app.database.db import SQLiteSubmissionStore
from app.database.models import ProcessedSubmissionRecord
from app.github.publisher import GitHubPublisherService
from app.leetcode.detector import LeetCodeDetector
from app.linkedin.publisher import LinkedInPublisher


@dataclass(slots=True)
class WorkflowResult:
    status: str
    submission_id: str | None = None
    title: str | None = None
    topic: str | None = None
    github_status: str | None = None
    github_commit: str | None = None
    linkedin_status: str | None = None
    github_error: str | None = None
    linkedin_error: str | None = None
    error: str | None = None


T = TypeVar("T")


class WorkflowService:
    def __init__(
        self,
        store: SQLiteSubmissionStore,
        detector: LeetCodeDetector,
        ai_generator: AIContentGenerator,
        github_publisher: GitHubPublisherService,
        linkedin_publisher: LinkedInPublisher,
        logger: Logger | None = None,
        retry_attempts: int = 3,
        retry_backoff_seconds: float = 1.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.store = store
        self.detector = detector
        self.ai_generator = ai_generator
        self.github_publisher = github_publisher
        self.linkedin_publisher = linkedin_publisher
        self.logger = logger or getLogger(__name__)
        self.retry_attempts = retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds
        self.sleeper = sleeper

    def _retry(self, label: str, action: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                return action()
            except Exception as exc:  # pragma: no cover - exercised through higher-level tests
                last_error = exc
                self.logger.warning("%s attempt %s/%s failed: %s", label, attempt, self.retry_attempts, exc)
                if attempt < self.retry_attempts:
                    self.sleeper(self.retry_backoff_seconds * attempt)
        assert last_error is not None
        raise last_error

    def run_once(self) -> WorkflowResult:
        self.logger.info("poll started")
        submission = self.detector.detect_latest_accepted_submission()
        if submission is None:
            return WorkflowResult(status="idle")

        self.logger.info("submission detected submission_id=%s title=%s", submission.id, submission.title)
        existing = self.store.get(submission.id)
        if existing is not None:
            return WorkflowResult(
                status="skipped",
                submission_id=submission.id,
                title=submission.title,
                github_status=existing.github_status,
                github_commit=existing.github_commit,
                linkedin_status=existing.linkedin_status,
                github_error=existing.github_error,
                linkedin_error=existing.linkedin_error,
            )

        try:
            self.logger.info("ai generation started submission_id=%s", submission.id)
            ai_response = self.ai_generator.generate(submission)
            self.logger.info("ai generation completed submission_id=%s", submission.id)
        except Exception as exc:
            self.logger.exception("ai generation failed submission_id=%s", submission.id)
            return WorkflowResult(status="failed", submission_id=submission.id, title=submission.title, error=str(exc))

        github_commit: str | None = None
        github_status = "pending"
        linkedin_status = "pending"
        github_error: str | None = None
        linkedin_error: str | None = None

        try:
            github_result = self._retry("github publication", lambda: self.github_publisher.publish(submission, ai_response))
            github_commit = github_result.commit_sha
            github_status = "published"
            self.logger.info("github committed submission_id=%s topic=%s", submission.id, github_result.topic)
        except Exception as exc:
            github_status = "failed"
            github_error = str(exc)
            self.logger.exception("github publication failed submission_id=%s", submission.id)

        try:
            self._retry("linkedin publication", lambda: self.linkedin_publisher.publish(ai_response.linkedin_post))
            linkedin_status = "published"
            self.logger.info("linkedin published submission_id=%s", submission.id)
        except Exception as exc:
            linkedin_status = "failed"
            linkedin_error = str(exc)
            self.logger.exception("linkedin publication failed submission_id=%s", submission.id)

        record = ProcessedSubmissionRecord(
            submission_id=submission.id,
            title=submission.title,
            github_status=github_status,
            github_commit=github_commit,
            linkedin_status=linkedin_status,
            github_error=github_error,
            linkedin_error=linkedin_error,
        )
        self.store.save(record)

        if github_status == "failed" or linkedin_status == "failed":
            return WorkflowResult(
                status="partial_failure",
                submission_id=submission.id,
                title=submission.title,
                topic=ai_response.topic,
                github_status=github_status,
                github_commit=github_commit,
                linkedin_status=linkedin_status,
                github_error=github_error,
                linkedin_error=linkedin_error,
                error="github_failed" if github_status == "failed" else "linkedin_failed",
            )

        return WorkflowResult(
            status="succeeded",
            submission_id=submission.id,
            title=submission.title,
            topic=ai_response.topic,
            github_status=github_status,
            github_commit=github_commit,
            linkedin_status=linkedin_status,
        )
