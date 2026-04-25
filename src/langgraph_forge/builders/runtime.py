"""Runtime helpers for replay (counterfactual fork supported).

`replay` wraps LangGraph's ``aupdate_state`` + ``ainvoke`` idioms
behind ``ThreadConfig`` so users do not memorise the
``{"configurable": {"thread_id": ..., "checkpoint_id": ...}}`` shape
when re-running from a checkpoint, with optional state modification
for counterfactual analysis.

Resume-after-interrupt was removed in 0.3.0a1 because the helper
body was a single ``Command(resume=value)`` call -- pure 1-line
sugar with no semantic carry. The upstream idiom is documented in
``docs/how-to/resume-after-interrupt.md``; users import
``langgraph.types.Command`` directly.

`replay` is infrastructure (Line 2 of the project boundary): it
manipulates the graph's runtime config but never reasons about it.
Domain decisions about *which* counterfactual to fork to are the
user's call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
