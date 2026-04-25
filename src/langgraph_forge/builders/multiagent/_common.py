"""Shared helpers for multi-agent pattern factories.

Every pattern factory in this subpackage (supervisor, swarm,
hierarchical, router, custom) needs to convert a
:class:`SpecialistSpec` into a graph node before wiring the
topology. Putting that conversion here -- in one place -- is the
"no-rework" guarantee from ADR-0006: adding a sixth pattern reuses
this helper rather than re-implementing it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.prebuilt import create_react_agent

from langgraph_forge.builders.llm import get_model

if TYPE_CHECKING:
    from langgraph_forge.core.specs import SpecialistSpec


def specialist_to_node(spec: SpecialistSpec) -> object:
    """Convert a SpecialistSpec into a graph node (CompiledStateGraph).

    Dispatches on the spec's encoding (validated by the spec itself):

    - **ReAct mode** (``prompt + model`` set) -- builds a ReAct worker
      via ``langgraph.prebuilt.create_react_agent``, sourcing the
      chat model through :func:`langgraph_forge.builders.llm.get_model`.
      Routing the model through ``get_model`` keeps the
      ``spec -> chat-model`` path singular across the codebase.

    - **Subgraph mode** (``subgraph`` set) -- returns the supplied
      compiled graph unchanged. The subgraph encapsulates its own
      behaviour (deterministic Python, another factory's output for
      hierarchical composition, etc.). No LLM is constructed; the
      graph runs as-is.

    Returns the node object as ``CompiledStateGraph`` (typed as
    ``object`` to keep this module independent of upstream's
    compiled-graph type at import time).
    """
    if spec.subgraph is not None:
        return spec.subgraph

    # ReAct mode: validator guarantees prompt and model are not None when
    # subgraph is None, so the assertions document a cross-field
    # invariant for type checkers without changing runtime behaviour.
    assert spec.prompt is not None  # noqa: S101 -- validator-enforced
    assert spec.model is not None  # noqa: S101 -- validator-enforced
    return create_react_agent(
        model=get_model(spec.model),
        tools=spec.tools,
        prompt=spec.prompt,
        name=spec.name,
    )
