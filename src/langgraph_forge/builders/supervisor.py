"""Supervisor + specialists factory, backed by ``langgraph-supervisor``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from langgraph_forge.builders.llm import get_model
from langgraph_forge.core.specs import SpecialistSpec

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph


def create_supervisor_agent(
    *,
    supervisor_model: BaseChatModel,
    specialists: list[SpecialistSpec],
    supervisor_prompt: str,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Compile a supervisor graph with ReAct specialist workers.

    For each :class:`SpecialistSpec` we construct a ReAct worker whose
    ``name`` is the spec's routing key, then hand the list of workers
    to :func:`langgraph_supervisor.create_supervisor`. The supervisor's
    own LLM (``supervisor_model``) orchestrates delegation; it is
    deliberately separate from the specialist models so a cheap Haiku
    supervisor can route to Sonnet workers (or vice-versa).

    The resulting graph is compiled with the optional checkpointer so
    the returned object is ready to ``ainvoke``.
    """
    workers = [
        create_react_agent(
            model=get_model(spec.model),
            tools=spec.tools,
            prompt=spec.prompt,
            name=spec.name,
        )
        for spec in specialists
    ]

    # Upstream's `create_supervisor` annotates `agents` as `list[Pregel]`,
    # but `create_react_agent` returns `CompiledStateGraph` which is a
    # Pregel subclass. Pyright cannot see that without explicit Variance
    # markers in upstream. Runtime path works; unit tests cover composition.
    supervisor_graph = create_supervisor(
        agents=workers,  # pyright: ignore[reportArgumentType]
        model=supervisor_model,
        prompt=supervisor_prompt,
    )

    return supervisor_graph.compile(checkpointer=checkpointer)
