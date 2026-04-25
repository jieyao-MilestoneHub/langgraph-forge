"""Runtime helpers for replay + resume.

These wrap LangGraph's ainvoke + Command(resume=...) idioms behind
``ThreadConfig`` so users do not memorise the
``{"configurable": {"thread_id": ..., "checkpoint_id": ...}}`` shape
or the ``Command`` import path.

Both helpers are infrastructure (Line 2 of the project boundary):
they manipulate the graph's runtime config but never reason about
it. Domain decisions about *what* to resume with or *which*
counterfactual to fork to are the user's call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.types import Command

if TYPE_CHECKING:
    from langgraph_forge.core.specs import ThreadConfig


async def replay(
    graph: Any,
    thread: ThreadConfig,
    *,
    modify: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-run a graph from a checkpoint, optionally with a state modification.

    With ``modify=None``, this is a pure replay -- LangGraph re-executes
    from ``thread.checkpoint_id`` (or the latest checkpoint if not
    specified). With ``modify`` set, the helper first writes the
    supplied dict via :meth:`graph.aupdate_state` (a counterfactual
    fork) and then ainvokes from that branch.

    The graph object is duck-typed (any object exposing ``ainvoke`` and
    optionally ``aupdate_state``) to avoid a hard import dependency
    on a specific compiled-graph type.
    """
    config = thread.to_langgraph()
    if modify is not None:
        await graph.aupdate_state(config, modify)
    return await graph.ainvoke(None, config)


async def resume(graph: Any, thread: ThreadConfig, value: Any) -> dict[str, Any]:
    """Resume an interrupted graph with the supplied human-in-the-loop value.

    Wraps the ``Command(resume=value)`` idiom so callers do not need
    to import ``langgraph.types.Command`` themselves. ``value`` flows
    into whatever ``interrupt(...)`` call site the graph paused at;
    its shape is the user's contract with their interrupt callers.
    """
    return await graph.ainvoke(Command(resume=value), thread.to_langgraph())
