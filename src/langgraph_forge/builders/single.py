"""Single-agent ReAct factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.prebuilt import create_react_agent

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph.state import CompiledStateGraph


def create_single_agent(
    *,
    model: BaseChatModel,
    tools: list[BaseTool],
    prompt: str | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Build a compiled ReAct agent backed by LangGraph's prebuilt template.

    A keyword-only delegation to :func:`langgraph.prebuilt.create_react_agent`
    so users import one module (this one) instead of three
    (``langgraph.prebuilt`` for the factory, ``langchain_core.tools`` for
    the tool type, their chosen provider chat class).

    Build the ``model`` via :func:`langgraph_forge.builders.llm.get_model` --
    this function does not touch provider wiring.

    .. note::
        ``interrupt_before`` / ``interrupt_after`` are **not** supported
        by this factory: ``langgraph.prebuilt.create_react_agent``
        compiles its own internal graph and does not expose those
        knobs upstream. For HITL workflows on a single ReAct node,
        use :func:`langgraph_forge.create_custom_agent` and author the
        node yourself; you then pass ``interrupt_before`` /
        ``interrupt_after`` into ``create_custom_agent``. See
        ``docs/explanation/initialization-boundary.md`` § Line 2 for
        the full rationale (the asymmetry is upstream-driven, not a
        design choice).
    """
    return create_react_agent(
        model=model,
        tools=tools,
        prompt=prompt,
        checkpointer=checkpointer,
    )
