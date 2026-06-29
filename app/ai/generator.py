from __future__ import annotations

from typing import Any

from app.ai.formatter import parse_ai_response
from app.ai.models import AIResponse
from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.leetcode.models import Submission


class AIContentGenerator:
    def generate(self, submission: Submission) -> AIResponse:  # pragma: no cover - interface
        raise NotImplementedError


class DisabledAIContentGenerator(AIContentGenerator):
    def generate(self, submission: Submission) -> AIResponse:
        raise RuntimeError("OpenAI is not configured")


class OpenAIResponsesGenerator(AIContentGenerator):
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini", client: Any | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self._client = client

    def generate(self, submission: Submission) -> AIResponse:
        client = self._client or self._build_client()
        response = client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(submission)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "leetbit_ai_response",
                    "schema": AIResponse.model_json_schema(),
                    "strict": True,
                }
            },
        )
        return parse_ai_response(self._extract_output_text(response))

    def _build_client(self) -> Any:
        from openai import OpenAI

        return OpenAI(api_key=self.api_key)

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        output_chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    output_chunks.append(text)
        if not output_chunks:
            raise ValueError("OpenAI response did not include text output")
        return "".join(output_chunks)
