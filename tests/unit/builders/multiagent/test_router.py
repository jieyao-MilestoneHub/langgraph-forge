"""Tests for langgraph_forge.builders.multiagent.router."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from langgraph_forge.builders.multiagent.router import create_router_agent
from langgraph_forge.core.specs import (
    ModelSpec,
    RouterSpec,
    RouteSpec,
    SpecialistSpec,
)


@pytest.fixture(autouse=True)
def _mock_get_model() -> Iterator[MagicMock]:
    # specialist_to_node calls _common.get_model whenever a route target
    # is a ReAct specialist. Without a real provider, init_chat_model
    # would fail. Auto-mock at _common's import boundary so every router
    # test can use ReAct-mode specialists cheaply.
    with patch(
        "langgraph_forge.builders.multiagent._common.get_model",
        return_value=MagicMock(),
    ) as mock:
        yield mock


def _model() -> ModelSpec:
    return ModelSpec(model="gpt-4o", provider="openai")


def _specialist(name: str = "alpha") -> SpecialistSpec:
    return SpecialistSpec(name=name, prompt="p", model=_model())


def _route(name: str = "billing") -> RouteSpec:
    return RouteSpec(
        name=name,
        description=f"Handles {name} requests.",
        target=_specialist(f"{name}_handler"),
    )


class TestClassifierTypeValidation:
    def test_llm_classifier_requires_prompt(self) -> None:
        spec = RouterSpec(routes=[_route()])

        with pytest.raises(ValueError, match="classifier_prompt"):
            create_router_agent(spec, classifier=_model())

    def test_invalid_classifier_type_rejected(self) -> None:
        spec = RouterSpec(routes=[_route()])

        with pytest.raises(TypeError, match="classifier"):
            create_router_agent(
                spec,
                classifier="not a model or callable",  # type: ignore[arg-type]
            )

    def test_empty_routes_rejected(self) -> None:
        with pytest.raises(ValueError, match="route"):
            create_router_agent(
                RouterSpec(routes=[]),
                classifier=lambda state: "x",  # noqa: ARG005
            )


class TestCallableClassifierBuildsGraph:
    def test_factory_compiles_with_callable_classifier(self) -> None:
        # End-to-end: a callable classifier + subgraph specialists
        # produces a compiled graph without touching any LLM.
        from langgraph.graph import END, START, StateGraph

        from langgraph_forge.core.state import RouterState

        # Build a tiny deterministic specialist via subgraph mode so we
        # do not need any real LLM. Each "specialist" appends a marker.
        def _make_passthrough(label: str) -> object:
            def node(state: RouterState) -> dict:
                return {"messages": [AIMessage(content=f"reached {label}")]}

            builder = StateGraph(RouterState)
            builder.add_node("passthrough", node)
            builder.add_edge(START, "passthrough")
            builder.add_edge("passthrough", END)
            return builder.compile()

        spec = RouterSpec(
            routes=[
                RouteSpec(
                    name="billing",
                    description="d",
                    target=SpecialistSpec(
                        name="billing", subgraph=_make_passthrough("billing")
                    ),
                ),
            ],
        )

        graph = create_router_agent(spec, classifier=lambda state: "billing")

        # Compiled graph exists; that is what the test asserts.
        assert graph is not None


class TestLLMClassifierBuildsGraph:
    def test_llm_classifier_produces_compiled_graph(self) -> None:
        # Use a subgraph specialist so specialist_to_node does not call
        # create_react_agent (which emits a 1.0 deprecation warning that
        # the suite treats as error).
        billing_subgraph = MagicMock(name="compiled_subgraph")
        spec = RouterSpec(
            routes=[
                RouteSpec(
                    name="billing",
                    description="Billing handler.",
                    target=SpecialistSpec(
                        name="billing", subgraph=billing_subgraph
                    ),
                )
            ],
        )

        with patch("langgraph_forge.builders.multiagent.router.get_model"):
            graph = create_router_agent(
                spec,
                classifier=_model(),
                classifier_prompt="Pick the route that matches the request.",
            )

        assert graph is not None


class TestCompileForwarding:
    def test_compiled_with_spec_checkpointer(self) -> None:
        fake_checkpointer = MagicMock(spec=BaseCheckpointSaver)
        spec = RouterSpec(
            routes=[_route()],
            checkpointer=fake_checkpointer,
        )
        # Patch both StateGraph and specialist_to_node: the former so we
        # can inspect compile() args, the latter to avoid going through
        # create_react_agent (which emits a deprecation warning under
        # LangGraph 1.0 that the test suite treats as an error).
        mock_state_graph_class = MagicMock()
        mock_builder = MagicMock()
        mock_state_graph_class.return_value = mock_builder
        with (
            patch(
                "langgraph_forge.builders.multiagent.router.StateGraph",
                mock_state_graph_class,
            ),
            patch(
                "langgraph_forge.builders.multiagent.router.specialist_to_node",
                return_value=MagicMock(),
            ),
        ):
            create_router_agent(spec, classifier=lambda state: "billing")

        _, kwargs = mock_builder.compile.call_args
        assert kwargs["checkpointer"] is fake_checkpointer

    def test_interrupts_pass_to_compile(self) -> None:
        spec = RouterSpec(
            routes=[_route("billing"), _route("tech")],
            interrupt_before=("billing",),
            interrupt_after=("tech",),
        )
        mock_state_graph_class = MagicMock()
        mock_builder = MagicMock()
        mock_state_graph_class.return_value = mock_builder
        with (
            patch(
                "langgraph_forge.builders.multiagent.router.StateGraph",
                mock_state_graph_class,
            ),
            patch(
                "langgraph_forge.builders.multiagent.router.specialist_to_node",
                return_value=MagicMock(),
            ),
        ):
            create_router_agent(spec, classifier=lambda state: "billing")

        _, kwargs = mock_builder.compile.call_args
        assert kwargs["interrupt_before"] == ["billing"]
        assert kwargs["interrupt_after"] == ["tech"]
