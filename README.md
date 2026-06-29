# Leetbit

Solve Once. Share Forever.

Leetbit watches for new accepted LeetCode submissions, turns them into structured documentation and a LinkedIn post, then publishes the artifacts through isolated adapters.

## Status

This repository now has a working first-pass implementation:

- FastAPI application entrypoint
- APScheduler wiring
- Configuration loading
- SQLite persistence layer
- LeetCode detection and parsing
- OpenAI Responses API adapter
- GitHub markdown publishing and push flow
- LinkedIn publishing adapter with API option
- Connected accounts with env fallback
- Workflow orchestration with independent failure tracking
- Account connection endpoints for GitHub OAuth device flow and LeetCode session capture

## Run locally

1. Create and activate a Python 3.12+ environment.
2. Install dependencies from `requirements.txt`.
3. Set the environment variables required by `app.config.Settings`.
4. Start the app with Uvicorn.

Example:

```bash
uvicorn app.main:app --reload
```

## Run in Docker

```bash
docker build -t leetbit .
docker run --rm -p 8000:8000 --env-file .env leetbit
```

## Environment variables

- `OPENAI_API_KEY`
- `LEETCODE_USERNAME`
- `GITHUB_TOKEN`
- `GITHUB_REPO`
- `GITHUB_OAUTH_CLIENT_ID`
- `GITHUB_OAUTH_SCOPE`
- `LINKEDIN_CONFIG`
- `POLL_INTERVAL`
- `DATABASE_URL`
- `LEETCODE_SESSION`
- `GITHUB_BASE_BRANCH`
- `GITHUB_BASE_PATH`

## Environment template

Create a local `.env` from this shape:

```env
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4.1-mini

LEETCODE_USERNAME=your-leetcode-username
LEETCODE_SESSION=your-leetcode-session-cookie

GITHUB_TOKEN=your-github-token
GITHUB_REPO=owner/repo
GITHUB_OAUTH_CLIENT_ID=your-github-oauth-client-id
GITHUB_OAUTH_SCOPE=repo
GITHUB_BASE_BRANCH=main
GITHUB_BASE_PATH=Leetbit-Revisions

LINKEDIN_CONFIG={"provider":"api","publish_url":"https://your-publisher-endpoint"}

DATABASE_URL=sqlite:///./leetbit.db
POLL_INTERVAL=300
LOG_LEVEL=INFO
```

## Notes

The workflow is intentionally adapter-driven so GitHub and LinkedIn can evolve independently without changing the core orchestration service.

## Connected accounts

Leetbit now supports connected accounts through the API so users do not have to keep secrets in shell config.

- `POST /auth/github/device/start` begins GitHub OAuth device flow when `GITHUB_OAUTH_CLIENT_ID` is configured.
- `POST /auth/github/device/complete` exchanges the device code for an access token and stores it in SQLite.
- `POST /auth/leetcode/connect` stores a LeetCode username and session cookie in SQLite.
- `GET /auth/status` shows the connected account state and env fallback state.

## Browser helper

The `browser-extension/` folder contains a small Chrome or Edge extension that reads the active `LEETCODE_SESSION` cookie after you sign in and posts it to the backend.
