"""Supervisor multi-agent factory, backed by ``langgraph-supervisor``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph_supervisor import create_supervisor

from langgraph_forge.builders.multiagent._common import specialist_to_node

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.graph.state import CompiledStateGraph

    from langgraph_forge.core.specs import MultiAgentSpec


def create_supervisor_agent(
    spec: MultiAgentSpec,
    *,
    supervisor_model: BaseChatModel,
    supervisor_prompt: str,
) -> CompiledStateGraph:
    """Compile a supervisor graph from a :class:`MultiAgentSpec`.

    Topology: each specialist in ``spec.specialists`` becomes a worker
    node (ReAct or subgraph, picked by :func:`specialist_to_node`).
    The supervisor LLM (``supervisor_model``) reads state each turn,
    issues a ``delegate_to_<name>`` tool call to pick the next worker,
    and incorporates the worker's reply.

    Cross-cutting concerns honoured:

    - **Persistence** -- ``spec.checkpointer`` is forwarded to
      ``compile(checkpointer=...)``. Pass any ``BaseCheckpointSaver``
      (or ``None`` for in-memory).
    - **Interrupts** -- ``spec.interrupt_before`` and
      ``spec.interrupt_after`` declare static pause points by node
      name; ``compile()`` enforces them at runtime.
    - **State schema** -- ``spec.state_schema`` is consumed by
      ``langgraph_supervisor`` internally; supply any ``ForgeState``
      subclass to add domain channels.
    """
    workers = [specialist_to_node(s) for s in spec.specialists]

    # Upstream's `create_supervisor` annotates `agents` as `list[Pregel]`,
    # but `create_react_agent` returns `CompiledStateGraph` (a Pregel
    # subclass) and a subgraph specialist is also a CompiledStateGraph.
    # Pyright cannot see the variance without explicit upstream markers.
    supervisor_graph = create_supervisor(
        agents=workers,  # pyright: ignore[reportArgumentType]
        model=supervisor_model,
        prompt=supervisor_prompt,
    )

    # compile() expects mutable list[str] for interrupts; the spec stores
    # tuples for immutability. Convert at the boundary.
    return supervisor_graph.compile(
        checkpointer=spec.checkpointer,
        interrupt_before=list(spec.interrupt_before),
        interrupt_after=list(spec.interrupt_after),
    )
