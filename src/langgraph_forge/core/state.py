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
    """Single-channel base; subclass to add domain channels::

    class MyState(ForgeState):
        plan: list[str]
    """

    messages: Annotated[list, add_messages]


class SwarmState(ForgeState):
    """Adds ``active_agent``: written by ``transfer_to_<peer>`` handoff tools, read by the swarm router to dispatch the next invocation."""

    active_agent: str | None


class RouterState(ForgeState):
    """Adds ``route``: written by the classifier node, read by the dispatch conditional edge.

    Stored in state (rather than a local variable) so checkpoint snapshots show which specialist ran -- useful for replay debugging.
    """

    route: str | None
