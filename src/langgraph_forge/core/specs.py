"""Declarative configuration types for langgraph-forge.

All specs are frozen Pydantic models: they serve as value objects that
users construct in code, diff in git, and pass to factory functions.
Mutating a spec after construction is a bug.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Self

from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    """Declarative specification of one reasoning slot in a multi-agent graph.

    Per the project boundary (Line 1, see
    ``docs/explanation/initialization-boundary.md``), a specialist slot
    accepts the user's domain reasoning in one of two encodings:

    1. **Live LLM (ReAct mode)** -- supply ``prompt`` + ``model`` (and
       optionally ``tools``). The factory builds a ReAct worker via
       ``langgraph.prebuilt.create_react_agent``.
    2. **Encoded code (subgraph mode)** -- supply ``subgraph``: any
       compiled ``CompiledStateGraph``, including a single deterministic
       node or another factory's output (used by hierarchical to slot
       a sub-supervisor here). The graph runs as-is without further
       wrapping.

    Mixed mode is rejected -- supplying both a top-level prompt / model /
    tools AND a subgraph is almost always a mistake (the subgraph
    encapsulates its own prompts and tools).

    ``name`` is the routing key the orchestrator uses
    (``delegate_to_<name>`` in supervisor, ``transfer_to_<name>`` in
    swarm) so it must be a valid Python-identifier-shaped token.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    name: str = Field(..., pattern=r"^[a-z][a-z0-9_]{0,63}$")
    prompt: str | None = None
    model: ModelSpec | None = None
    tools: list[BaseTool] = Field(default_factory=list)
    subgraph: Any | None = None  # CompiledStateGraph; typed as Any to avoid
    #                              # importing langgraph.graph.state at module
    #                              # load and to keep tests cheap to author.

    @model_validator(mode="after")
    def _validate_encoding(self) -> Self:
        if self.subgraph is not None:
            # Subgraph mode: prompt / model / tools are not allowed --
            # the subgraph encapsulates its own behaviour.
            if self.prompt is not None:
                raise ValueError("subgraph mode does not accept prompt")
            if self.model is not None:
                raise ValueError("subgraph mode does not accept model")
            if self.tools:
                raise ValueError("subgraph mode does not accept tools")
            return self

        # ReAct mode requires both prompt and model. Either alone is an
        # incomplete encoding -- the error message names all three viable
        # completions so the user sees their options.
        if self.prompt is None or self.model is None:
            raise ValueError(
                "specialist must declare an encoding: provide prompt + model "
                "(ReAct mode) OR subgraph (encoded mode)"
            )
        return self


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
                raise ValueError(f"transport={self.transport} does not accept `command`")
        return self


class MCPConfig(BaseModel):
    """Aggregate configuration for all MCP servers an agent may reach.

    Maps a caller-chosen logical name (used in logs and allowlists) to
    a :class:`MCPServerConfig`. The mapping is frozen: to change the
    topology, construct a new MCPConfig.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    servers: dict[str, MCPServerConfig]


class MultiAgentSpec(BaseModel):
    """Topology-agnostic configuration consumed by every multi-agent factory.

    Pattern-specific extras (supervisor_prompt, default_active_agent,
    classifier model) ride as keyword arguments to the factory and
    deliberately do NOT live on this spec -- otherwise every pattern
    would have to ignore the irrelevant fields, and the spec would
    grow into convilyn-style envelope territory.

    Each field maps to a layer of the project boundary
    (see ``docs/explanation/initialization-boundary.md``):

    - ``specialists`` -- the reasoning slots (Line 1). Each
      SpecialistSpec inside chooses LLM ReAct or encoded subgraph.
    - ``state_schema`` -- typed channels (Line 2 infrastructure).
      Defaults to ForgeState (just messages). Subclass to add domain
      channels.
    - ``checkpointer`` -- persistence infrastructure (Line 2).
    - ``interrupt_before`` / ``interrupt_after`` -- static interrupt
      declarations (Line 2 infrastructure); the factory passes them
      to graph.compile().
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    specialists: list[SpecialistSpec]
    # state_schema typed as Any rather than `type` because (a) the field's
    # actual default is set by the model_validator below (None gets filled
    # to ForgeState), and (b) pyright cannot meaningfully narrow to
    # "this is a TypedDict class" without a Protocol upstream does not
    # provide. Run-time the value is always a TypedDict subclass.
    state_schema: Any = Field(default=None)
    checkpointer: BaseCheckpointSaver | None = None
    interrupt_before: tuple[str, ...] = ()
    interrupt_after: tuple[str, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _default_state_schema(cls, data: Any) -> Any:
        # ForgeState is in core.state which would create a circular import
        # if imported at module top-level; resolve here.
        if isinstance(data, dict) and data.get("state_schema") is None:
            from langgraph_forge.core.state import ForgeState  # noqa: PLC0415

            data["state_schema"] = ForgeState
        return data


@dataclass(frozen=True, slots=True)
class ThreadConfig:
    """Typed wrapper around the LangGraph runtime configurable dict.

    LangGraph's runtime config carries thread isolation, namespace
    scoping, and replay targeting in a nested dict::

        {"configurable": {"thread_id": ..., "checkpoint_ns": ..., "checkpoint_id": ...}}

    Memorising that shape and getting the keys right every call is a
    typo magnet (``thread-id`` vs ``thread_id``, missing the
    ``configurable`` wrapper). :class:`ThreadConfig` makes the
    intent typed and immutable: construct it once per
    thread / namespace / replay target, then call :meth:`to_langgraph`
    when handing it to ``graph.ainvoke`` / ``graph.astream`` /
    :func:`langgraph_forge.builders.runtime.replay`.

    A frozen :class:`dataclasses.dataclass` (rather than a Pydantic
    model) because the surface is one method and three primitive
    fields; pulling Pydantic in for that is over-engineering.
    """

    thread_id: str
    checkpoint_ns: str = ""
    checkpoint_id: str | None = None

    def to_langgraph(self) -> dict[str, Any]:
        """Render the LangGraph configurable dict.

        ``checkpoint_id`` is omitted when None so the graph treats the
        invocation as "continue this thread" rather than "replay from
        a specific checkpoint".
        """
        configurable: dict[str, Any] = {
            "thread_id": self.thread_id,
            "checkpoint_ns": self.checkpoint_ns,
        }
        if self.checkpoint_id is not None:
            configurable["checkpoint_id"] = self.checkpoint_id
        return {"configurable": configurable}
