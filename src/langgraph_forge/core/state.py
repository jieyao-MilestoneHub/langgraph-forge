"""Graph state schemas.

Per the project boundary (Line 2 in
``docs/explanation/initialization-boundary.md``), state types ship
**only** the channels each topology itself needs to function. Domain
fields (``task``, ``intent``, ``constraints``, ``risk_level``,
``artifacts``) are user code -- subclass the appropriate base.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class ForgeState(TypedDict):
    """Minimal state schema carrying message history under LangGraph's reducer.

    Users with additional channels (scratchpad, plan, domain envelope)
    subclass this TypedDict rather than editing it in-place, so the base
    contract stays stable::

        class MyState(ForgeState):
            plan: list[str]
    """

    messages: Annotated[list, add_messages]


class SwarmState(ForgeState):
    """Swarm-pattern state schema.

    Adds ``active_agent`` to track which specialist currently holds
    the turn. Handoff tools (``transfer_to_<peer>``) update this
    field; the swarm router uses its value to dispatch the next
    invocation.

    Subclasses inherit ``messages`` from :class:`ForgeState` and may
    add domain channels alongside ``active_agent``.
    """

    active_agent: str | None


class RouterState(ForgeState):
    """Router-pattern state schema.

    Adds ``route`` to record which specialist the classifier dispatched
    to. The classifier writes this field; the conditional edge reads it
    to pick the next node. Persisting ``route`` in state (rather than
    an internal-only variable) makes replay debugging easy: a checkpoint
    snapshot shows exactly which specialist ran.

    Subclasses inherit ``messages`` from :class:`ForgeState` and may
    add domain channels alongside ``route``.
    """

    route: str | None
