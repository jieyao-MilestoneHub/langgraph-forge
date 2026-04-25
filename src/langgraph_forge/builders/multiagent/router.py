"""Router multi-agent factory: classifier dispatches once, no loop."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from langgraph_forge.builders.llm import get_model
from langgraph_forge.builders.multiagent._common import specialist_to_node
from langgraph_forge.core.specs import ModelSpec, RouterSpec
from langgraph_forge.core.state import RouterState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


# Public type alias for the classifier slot. Per Line 1 of the boundary,
# a reasoning slot accepts either a live LLM (ModelSpec) or encoded code
# (a Callable). Both are first-class equals in the router pattern.
ClassifierSlot = ModelSpec | Callable[[Any], str]


def create_router_agent(
    spec: RouterSpec,
    *,
    classifier: ClassifierSlot,
    classifier_prompt: str | None = None,
) -> CompiledStateGraph:
    """Compile a router graph from a :class:`RouterSpec`.

    Topology: ``START -> classifier -> conditional_edge -> specialist[i] -> END``.
    There is no loop back to the classifier; once a specialist runs, the
    graph terminates. Use a supervisor pattern if you need iterative
    re-routing.

    The classifier slot accepts the user's domain reasoning in two
    encodings:
    - A :class:`ModelSpec` (live LLM): the factory builds an LLM call
      that takes the route descriptions plus the latest user message
      and returns a route name. ``classifier_prompt`` is required.
    - A ``Callable[[State], str]`` (encoded code): the factory invokes
      the callable with the current state; whatever it returns is the
      route name. ``classifier_prompt`` is ignored.

    Cross-cutting concerns flow through ``spec`` (checkpointer,
    interrupt_before / after) and land on ``compile()``.
    """
    if not spec.routes:
        raise ValueError("RouterSpec must declare at least one route")

    classifier_node = _build_classifier_node(spec, classifier, classifier_prompt)

    builder = StateGraph(RouterState)
    # Pyright cannot infer that our dict-shaped node callables and the
    # CompiledStateGraph returned by specialist_to_node both satisfy
    # add_node's generic StateNode bound; same situation as supervisor.py.
    builder.add_node("classifier", classifier_node)  # pyright: ignore[reportArgumentType]
    for route in spec.routes:
        target_node = specialist_to_node(route.target)
        builder.add_node(route.name, target_node)  # pyright: ignore[reportArgumentType]
        builder.add_edge(route.name, END)

    builder.add_edge(START, "classifier")

    route_names = {r.name for r in spec.routes}
    default_route = spec.default_route

    def _dispatch(state: dict[str, Any]) -> str:
        chosen = state.get("route")
        if chosen in route_names:
            return chosen
        if default_route and default_route in route_names:
            return default_route
        return END

    builder.add_conditional_edges(
        "classifier",
        _dispatch,
        [*list(route_names), END],
    )

    return builder.compile(
        checkpointer=spec.checkpointer,
        interrupt_before=list(spec.interrupt_before),
        interrupt_after=list(spec.interrupt_after),
    )


def _build_classifier_node(
    spec: RouterSpec,
    classifier: ClassifierSlot,
    classifier_prompt: str | None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Pick the right classifier-node implementation based on encoding."""
    if isinstance(classifier, ModelSpec):
        if classifier_prompt is None:
            raise ValueError(
                "LLM classifier mode requires classifier_prompt; "
                "supply a Callable instead if no prompt is meaningful"
            )
        return _llm_classifier_node(classifier, classifier_prompt, spec)
    if callable(classifier):
        return _callable_classifier_node(classifier)
    raise TypeError(
        f"classifier must be ModelSpec or Callable[[State], str], got {type(classifier).__name__}"
    )


def _callable_classifier_node(
    classifier: Callable[[Any], str],
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Wrap a user-supplied callable so it returns a state update."""

    def node(state: dict[str, Any]) -> dict[str, Any]:
        return {"route": classifier(state)}

    return node


def _llm_classifier_node(
    model_spec: ModelSpec,
    prompt: str,
    spec: RouterSpec,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a node that asks an LLM to pick a route name.

    The LLM sees the user-supplied classifier_prompt, the route
    descriptions, and the most recent user message. We parse the
    response by lowercase substring match for any known route name --
    deliberately permissive so phrasing like "I'd pick billing"
    still resolves. If no match is found, the node sets route=None
    and the graph's dispatch falls back to spec.default_route or END.
    """
    route_descriptions = "\n".join(f"- {r.name}: {r.description}" for r in spec.routes)
    full_prompt = (
        f"{prompt}\n\nAvailable routes:\n{route_descriptions}\n\n"
        "Return only the name of the route that best matches."
    )
    route_names = [r.name for r in spec.routes]

    def node(state: dict[str, Any]) -> dict[str, Any]:
        chat_model = get_model(model_spec)
        messages = state.get("messages") or []
        last_msg = messages[-1].content if messages else ""
        response = chat_model.invoke(
            [HumanMessage(content=f"{full_prompt}\n\nMessage: {last_msg}")]
        )
        text = (getattr(response, "content", "") or "").lower().strip()
        for name in route_names:
            if name in text:
                return {"route": name}
        return {"route": None}

    return node
