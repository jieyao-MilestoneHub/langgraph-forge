"""Default graph state schema for langgraph-forge agents."""

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
