from __future__ import annotations

from pydantic import BaseModel, Field


class AgentDefinition(BaseModel):
    name: str
    display_name: str = Field(alias="displayName", default="")
    output_file: str = Field(alias="outputFile", default="")
    tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(alias="disallowedTools", default_factory=list)
    max_turns: int = Field(alias="maxTurns", default=40)
    max_tokens: int | None = Field(alias="maxTokens", default=None)
    model: str | None = None
    temperature: float = 0.7
    prompt: str = ""

    model_config = {"populate_by_name": True}
