from __future__ import annotations

from dataclasses import asdict, dataclass

from fastapi import FastAPI, HTTPException

from app.ai.generator import DisabledAIContentGenerator, OpenAIResponsesGenerator
from app.config import Settings, get_settings
from app.database.db import SQLiteSubmissionStore
from app.github.git import GitRepositoryManager, build_github_remote_url
from app.github.publisher import GitHubPublisherService
from app.leetcode.detector import LeetCodeDetector
from app.leetcode.graphql import LeetCodeGraphQLClient
from app.linkedin.publisher import DisabledLinkedInPublisher, build_linkedin_publisher
from app.scheduler.scheduler import LeetbitScheduler
from app.services.workflow import WorkflowService
from app.utils.logging import configure_logging


@dataclass(slots=True)
class AppRuntime:
    settings: Settings
    store: SQLiteSubmissionStore
    workflow: WorkflowService
    scheduler: LeetbitScheduler
    leetcode_client: LeetCodeGraphQLClient | None = None

    def close(self) -> None:
        self.scheduler.shutdown()
        if self.leetcode_client is not None:
            self.leetcode_client.close()
        self.store.close()


def build_runtime(settings: Settings) -> AppRuntime:
    configure_logging(settings.log_level)

    store = SQLiteSubmissionStore(settings.database_url)

    leetcode_client: LeetCodeGraphQLClient | None = None
    detector = LeetCodeDetector(None)
    if settings.leetcode_username:
        leetcode_client = LeetCodeGraphQLClient(
            username=settings.leetcode_username,
            session_cookie=settings.leetcode_session,
        )
        detector = LeetCodeDetector(leetcode_client)

    ai_generator = DisabledAIContentGenerator()
    if settings.openai_api_key:
        ai_generator = OpenAIResponsesGenerator(api_key=settings.openai_api_key, model=settings.openai_model)

    repository_manager = GitRepositoryManager(
        settings.github_base_path,
        settings.github_base_branch,
        build_github_remote_url(settings.github_repo, settings.github_token),
    )
    github_publisher = GitHubPublisherService(repository_manager)

    linkedin_publisher = build_linkedin_publisher(settings.linkedin_config)
    if linkedin_publisher is None:
        linkedin_publisher = DisabledLinkedInPublisher()

    workflow = WorkflowService(
        store=store,
        detector=detector,
        ai_generator=ai_generator,
        github_publisher=github_publisher,
        linkedin_publisher=linkedin_publisher,
    )
    scheduler = LeetbitScheduler(workflow=workflow, interval_seconds=settings.poll_interval)
    return AppRuntime(
        settings=settings,
        store=store,
        workflow=workflow,
        scheduler=scheduler,
        leetcode_client=leetcode_client,
    )


settings = get_settings()
runtime = build_runtime(settings)
app = FastAPI(title="Leetbit", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    runtime.scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    runtime.close()


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/workflow/run")
def run_workflow() -> dict[str, object]:
    result = runtime.workflow.run_once()
    return asdict(result)


@app.get("/workflow/last")
def workflow_state() -> dict[str, object]:
    latest = runtime.store.latest()
    if latest is None:
        raise HTTPException(status_code=404, detail="No processed submissions found")
    return {
        "submission_id": latest.submission_id,
        "title": latest.title,
        "processed_at": latest.processed_at.isoformat(),
        "github_commit": latest.github_commit,
        "linkedin_status": latest.linkedin_status,
    }
