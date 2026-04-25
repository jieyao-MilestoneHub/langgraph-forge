"""Swarm multi-agent factory, backed by ``langgraph-swarm``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph_swarm import create_swarm

from langgraph_forge.builders.multiagent._common import specialist_to_node
from langgraph_forge.core.state import ForgeState, SwarmState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from langgraph_forge.core.specs import MultiAgentSpec


def create_swarm_agent(
    spec: MultiAgentSpec,
    *,
    default_active_agent: str,
) -> CompiledStateGraph:
    """Compile a swarm graph from a :class:`MultiAgentSpec`.

    Topology: each specialist becomes a worker via
    :func:`specialist_to_node`. Active control passes between
    specialists through ``transfer_to_<peer>`` tool calls; the
    ``active_agent`` channel in :class:`SwarmState` records who
    currently holds the turn.

    The user is responsible for adding handoff tools to each
    specialist (via ``langgraph_swarm.create_handoff_tool``)
    before constructing the spec -- the factory does not auto-
    inject them, because doing so would force the package to know
    which agents may hand off to which (a domain decision per
    Line 1 of the boundary).

    State schema dispatch: when ``spec.state_schema`` is the default
    :class:`ForgeState`, the factory swaps to :class:`SwarmState`
    so the upstream router has the ``active_agent`` field it
    requires. Any user-supplied schema (including custom subclasses
    of either base) is honoured untouched.

    Cross-cutting concerns honoured (mirrors supervisor):
    - ``spec.checkpointer`` -> compile(checkpointer=...).
    - ``spec.interrupt_before`` / ``interrupt_after`` -> compile().
    """
    workers = [specialist_to_node(s) for s in spec.specialists]

    state_schema = SwarmState if spec.state_schema is ForgeState else spec.state_schema

    workflow = create_swarm(
        agents=workers,  # pyright: ignore[reportArgumentType]
        default_active_agent=default_active_agent,
        state_schema=state_schema,
    )

    return workflow.compile(
        checkpointer=spec.checkpointer,
        interrupt_before=list(spec.interrupt_before),
        interrupt_after=list(spec.interrupt_after),
    )
