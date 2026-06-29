from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.ai.models import AIResponse
from app.github.git import GitRepositoryManager
from app.github.markdown import build_markdown_filename, classify_topic, render_markdown_document
from app.leetcode.models import Submission


@dataclass(slots=True)
class GitHubPublishResult:
    file_path: Path
    topic: str
    commit_sha: str | None


class GitHubPublisherService:
    def __init__(self, repository_manager: GitRepositoryManager) -> None:
        self.repository_manager = repository_manager

    def publish(self, submission: Submission, response: AIResponse) -> GitHubPublishResult:
        topic = classify_topic(submission, response)
        self.repository_manager.ensure_repository()

        target_directory = self.repository_manager.repository_path / topic
        target_directory.mkdir(parents=True, exist_ok=True)
        target_path = target_directory / build_markdown_filename(submission)
        target_path.write_text(render_markdown_document(submission, response), encoding="utf-8")

        commit_sha = self.repository_manager.commit_and_push(f"docs: add {submission.title}")
        return GitHubPublishResult(file_path=target_path, topic=topic, commit_sha=commit_sha)
