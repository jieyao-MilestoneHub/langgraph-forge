"""Declarative configuration types for langgraph-forge.

All specs are frozen Pydantic models: they serve as value objects that
users construct in code, diff in git, and pass to factory functions.
Mutating a spec after construction is a bug.
"""

from __future__ import annotations

from typing import Any, Literal

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self


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


class SpecialistSpec(BaseModel):
    """Declarative specification of one worker agent in a supervisor graph.

    Passed to :func:`langgraph_forge.builders.supervisor.create_supervisor_agent`,
    which turns each spec into a ReAct worker with the given model, tools,
    and system prompt. The ``name`` is the routing key the supervisor LLM
    uses (``delegate_to_<name>``) so it must be a valid Python-identifier-
    shaped token.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    name: str = Field(..., pattern=r"^[a-z][a-z0-9_]{0,63}$")
    prompt: str
    model: ModelSpec
    tools: list[BaseTool] = Field(default_factory=list)


class MCPServerConfig(BaseModel):
    """Connection details for one MCP server.

    Mirrors the dict shape accepted by
    :class:`langchain_mcp_adapters.client.MultiServerMCPClient`, plus
    cross-field validation that rules out nonsensical combinations
    (stdio + url, network transport + command) before a subprocess or
    network call is attempted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    transport: Literal["stdio", "sse", "streamable_http"]
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    url: str | None = None
    env: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_transport_fields(self) -> Self:
        if self.transport == "stdio":
            if self.command is None:
                raise ValueError("transport=stdio requires `command`")
            if self.url is not None:
                raise ValueError("transport=stdio does not accept `url`")
        else:  # sse or streamable_http
            if self.url is None:
                raise ValueError(f"transport={self.transport} requires `url`")
            if self.command is not None:
                raise ValueError(
                    f"transport={self.transport} does not accept `command`"
                )
        return self


class MCPConfig(BaseModel):
    """Aggregate configuration for all MCP servers an agent may reach.

    Maps a caller-chosen logical name (used in logs and allowlists) to
    a :class:`MCPServerConfig`. The mapping is frozen: to change the
    topology, construct a new MCPConfig.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    servers: dict[str, MCPServerConfig]
