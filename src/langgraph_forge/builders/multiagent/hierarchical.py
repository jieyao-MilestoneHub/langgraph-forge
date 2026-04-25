"""Hierarchical multi-agent factory: supervisor of team supervisors.

This module is intentionally short. Hierarchical multi-agent
topologies are pure composition over :func:`create_supervisor_agent`
plus :attr:`SpecialistSpec.subgraph`. There is no new wiring logic
here -- only the recursion that turns each :class:`TeamSpec` into a
compiled supervisor subgraph and slots it into the top-level
supervisor's specialists list.

Per ADR-0006: this is the structural "no rework" payoff. Adding a
seventh pattern in a future minor version reuses the same trick or
defines its own factory; either way, hierarchical never grew its
own wiring code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph_forge.builders.llm import get_model
from langgraph_forge.builders.multiagent.supervisor import create_supervisor_agent
from langgraph_forge.core.specs import MultiAgentSpec, SpecialistSpec

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph

    from langgraph_forge.core.specs import TeamSpec


def create_hierarchical_agent(
    *,
    top_supervisor_model: BaseChatModel,
    top_supervisor_prompt: str,
    teams: list[TeamSpec],
    checkpointer: BaseCheckpointSaver | None = None,
    interrupt_before: tuple[str, ...] = (),
    interrupt_after: tuple[str, ...] = (),
) -> CompiledStateGraph:
    """Compile a two-level supervisor hierarchy.

    Each :class:`TeamSpec` becomes a compiled supervisor subgraph
    (its own LLM, prompt, and specialists). The N team subgraphs
    are then wrapped as :class:`SpecialistSpec` entries with
    ``subgraph=`` set, and a top-level supervisor compiles over
    them. Persistence and interrupt declarations apply at the top
    level only -- per-team persistence belongs in user code.

    The factory does not take a ``MultiAgentSpec`` (unlike supervisor
    / swarm) because the top spec is constructed from ``teams`` and
    the cross-cutting kwargs in one go; exposing both layers as
    separate specs would muddle the user's mental model.
    """
    # Compile each team as its own supervisor subgraph.
    team_subgraphs = []
    for team in teams:
        team_compiled = create_supervisor_agent(
            MultiAgentSpec(specialists=team.specialists),
            supervisor_model=get_model(team.supervisor_model),
            supervisor_prompt=team.supervisor_prompt,
        )
        team_subgraphs.append(SpecialistSpec(name=team.name, subgraph=team_compiled))

    # Top supervisor over the team subgraphs.
    return create_supervisor_agent(
        MultiAgentSpec(
            specialists=team_subgraphs,
            checkpointer=checkpointer,
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after,
        ),
        supervisor_model=top_supervisor_model,
        supervisor_prompt=top_supervisor_prompt,
    )
