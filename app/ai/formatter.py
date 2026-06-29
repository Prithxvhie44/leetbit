from __future__ import annotations

import json
from collections.abc import Mapping
from textwrap import dedent
from typing import Any

from app.ai.models import AIResponse


def parse_ai_response(payload: str | Mapping[str, Any]) -> AIResponse:
    if isinstance(payload, Mapping):
        parsed = AIResponse.model_validate(payload)
    else:
        parsed = AIResponse.model_validate(json.loads(payload))
    return normalize_ai_response(parsed)


def normalize_ai_response(response: AIResponse) -> AIResponse:
    return AIResponse(
        summary=response.summary.strip(),
        approach=response.approach.strip(),
        time_complexity=response.time_complexity.strip(),
        space_complexity=response.space_complexity.strip(),
        linkedin_post=response.linkedin_post.strip(),
        markdown=dedent(response.markdown).strip(),
        topic=response.topic.strip(),
    )


def response_to_json(response: AIResponse) -> str:
    return response.model_dump_json(indent=2)
