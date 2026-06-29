from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.ai.generator import DisabledAIContentGenerator, OpenAIResponsesGenerator
from app.auth.github import GitHubOAuthDeviceFlow
from app.config import Settings, get_settings
from app.database.db import SQLiteSubmissionStore
from app.database.models import ConnectedAccountRecord
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


class LeetCodeConnectRequest(BaseModel):
    username: str = Field(min_length=1)
    session_cookie: str = Field(min_length=1)


class GitHubDeviceStartRequest(BaseModel):
    client_id: str | None = None
    scope: str | None = None


class GitHubDeviceCompleteRequest(BaseModel):
    client_id: str | None = None
    device_code: str = Field(min_length=1)
    expires_in: int = Field(gt=0)
    interval: int = Field(gt=0)


def _account_value(store: SQLiteSubmissionStore, provider: str, key: str) -> str | None:
    account = store.get_account(provider)
    if account is None:
        return None
    value = account.data.get(key)
    if value is None:
        return None
    return str(value).strip() or None


def build_runtime(settings: Settings) -> AppRuntime:
    configure_logging(settings.log_level)

    store = SQLiteSubmissionStore(settings.database_url)

    def resolve_leetcode_username() -> str | None:
        return _account_value(store, "leetcode", "username") or settings.leetcode_username

    def resolve_leetcode_session() -> str | None:
        return _account_value(store, "leetcode", "session_cookie") or settings.leetcode_session

    def resolve_github_remote_url() -> str | None:
        token = _account_value(store, "github", "access_token") or settings.github_token
        return build_github_remote_url(settings.github_repo, token)

    leetcode_client = LeetCodeGraphQLClient(
        username_provider=resolve_leetcode_username,
        session_cookie_provider=resolve_leetcode_session,
    )
    detector = LeetCodeDetector(leetcode_client)

    ai_generator = DisabledAIContentGenerator()
    if settings.openai_api_key:
        ai_generator = OpenAIResponsesGenerator(api_key=settings.openai_api_key, model=settings.openai_model)

    repository_manager = GitRepositoryManager(
        settings.github_base_path,
        settings.github_base_branch,
        remote_url_provider=resolve_github_remote_url,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    runtime.scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    runtime.close()


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/status")
def auth_status() -> dict[str, Any]:
    accounts = {
        account.provider: account.as_json()
        for account in runtime.store.list_accounts()
    }
    return {
        "accounts": accounts,
        "env": {
            "github_token": bool(runtime.settings.github_token),
            "leetcode_session": bool(runtime.settings.leetcode_session),
        },
        "github_oauth_configured": bool(runtime.settings.github_oauth_client_id),
    }


@app.post("/auth/leetcode/connect")
def connect_leetcode(payload: LeetCodeConnectRequest) -> dict[str, str]:
    runtime.store.upsert_account(
        ConnectedAccountRecord(
            provider="leetcode",
            data={
                "username": payload.username.strip(),
                "session_cookie": payload.session_cookie.strip(),
                "source": "extension",
            },
        )
    )
    return {"status": "connected", "provider": "leetcode"}


@app.delete("/auth/leetcode/connect")
def disconnect_leetcode() -> dict[str, str]:
    runtime.store.delete_account("leetcode")
    return {"status": "disconnected", "provider": "leetcode"}


@app.post("/auth/github/device/start")
def start_github_device_flow(payload: GitHubDeviceStartRequest) -> dict[str, Any]:
    client_id = (payload.client_id or runtime.settings.github_oauth_client_id or "").strip()
    if not client_id:
        raise HTTPException(status_code=400, detail="GITHUB_OAUTH_CLIENT_ID is required for GitHub OAuth")

    scope = (payload.scope or runtime.settings.github_oauth_scope or "repo").strip()
    device_flow = GitHubOAuthDeviceFlow(client_id=client_id, scope=scope)
    result = device_flow.start()
    device_flow.close()
    return asdict(result)


@app.post("/auth/github/device/complete")
def complete_github_device_flow(payload: GitHubDeviceCompleteRequest) -> dict[str, str]:
    client_id = (payload.client_id or runtime.settings.github_oauth_client_id or "").strip()
    if not client_id:
        raise HTTPException(status_code=400, detail="GITHUB_OAUTH_CLIENT_ID is required for GitHub OAuth")

    scope = runtime.settings.github_oauth_scope
    device_flow = GitHubOAuthDeviceFlow(client_id=client_id, scope=scope)
    try:
        access_token = device_flow.complete(payload.device_code, payload.expires_in, payload.interval)
    finally:
        device_flow.close()

    runtime.store.upsert_account(
        ConnectedAccountRecord(
            provider="github",
            data={
                "access_token": access_token,
                "scope": scope,
                "source": "device_flow",
            },
        )
    )
    return {"status": "connected", "provider": "github"}


@app.delete("/auth/github/connect")
def disconnect_github() -> dict[str, str]:
    runtime.store.delete_account("github")
    return {"status": "disconnected", "provider": "github"}


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
