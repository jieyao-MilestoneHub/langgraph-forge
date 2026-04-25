"""Custom multi-agent factory: thin escape hatch over ``StateGraph``.

This is the layer that exists for users whose topology does not fit
into supervisor / swarm / hierarchical / router. It enforces no
reasoning-slot conventions; the user authors nodes and edges directly.

Per ADR-0006, the cross-cutting concerns
(:class:`langgraph.checkpoint.base.BaseCheckpointSaver`,
``interrupt_before``, ``interrupt_after``) still flow through
``compile()`` kwargs -- so even an escape-hatch graph composes with
the rest of the package's persistence and human-in-the-loop
machinery.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from langgraph.graph import StateGraph

from langgraph_forge.core.state import ForgeState

if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph


def create_custom_agent(
    *,
    build: Callable[[StateGraph], None],
    state_schema: type = ForgeState,
    checkpointer: BaseCheckpointSaver | None = None,
    interrupt_before: tuple[str, ...] = (),
    interrupt_after: tuple[str, ...] = (),
) -> CompiledStateGraph:
    """Compile a user-authored topology with the package's compile() kwargs.

    The factory constructs an empty :class:`langgraph.graph.StateGraph`
    over ``state_schema`` and hands it to the ``build`` callback, which
    is free to add any nodes, edges, and conditional edges the topology
    requires (including START / END wiring). After ``build`` returns,
    the factory compiles with the supplied checkpointer and interrupt
    declarations and returns the compiled graph.

    The four named patterns (supervisor / swarm / hierarchical / router)
    cover the common cases. Reach for ``create_custom_agent`` when none
    of those topologies fit -- e.g., a parallel fan-out + reducer, a
    sequential planner -> verifier pipeline, or a graph that mixes
    deterministic and ReAct nodes in a non-pattern shape.
    """
    builder = StateGraph(state_schema)
    build(builder)
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=list(interrupt_before),
        interrupt_after=list(interrupt_after),
    )
