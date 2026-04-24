"""Declarative configuration types for langgraph-forge.

All specs are frozen Pydantic models: they serve as value objects that
users construct in code, diff in git, and pass to factory functions.
Mutating a spec after construction is a bug.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelSpec(BaseModel):
    """Declarative configuration for an LLM invocation.

    Passed to :func:`langgraph_forge.builders.llm.get_model`, which forwards
    the fields to :func:`langchain.chat_models.init_chat_model`. The extra
    dict is passthrough for provider-specific kwargs (max_tokens,
    top_p, region_name for Bedrock, etc.) so adding a new provider does
    not require editing this class.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str
    provider: str
    temperature: float = 0.2
    extra: dict[str, Any] = Field(default_factory=dict)
