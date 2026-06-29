from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    approach: str = Field(min_length=1)
    time_complexity: str = Field(min_length=1)
    space_complexity: str = Field(min_length=1)
    linkedin_post: str = Field(min_length=1)
    markdown: str = Field(min_length=1)
    topic: str = Field(min_length=1)
