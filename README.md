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
- LinkedIn publishing adapter with browser and API options
- Workflow orchestration with independent failure tracking

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
- `LINKEDIN_CONFIG`
- `POLL_INTERVAL`
- `DATABASE_URL`
- `LEETCODE_SESSION`
- `GITHUB_BASE_BRANCH`
- `GITHUB_BASE_PATH`

## Notes

The workflow is intentionally adapter-driven so GitHub and LinkedIn can evolve independently without changing the core orchestration service.
