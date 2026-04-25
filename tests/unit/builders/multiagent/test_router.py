"""Tests for langgraph_forge.builders.multiagent.router."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from langgraph_forge.builders.multiagent.router import create_router_agent
from langgraph_forge.core.specs import (
    ModelSpec,
    RouterSpec,
    RouteSpec,
    SpecialistSpec,
)
from langgraph_forge.core.state import RouterState


class TestClassifierTypeValidation:
    def test_llm_classifier_requires_prompt(
        self,
        model_spec: ModelSpec,
        make_route: Callable[..., RouteSpec],
    ) -> None:
        spec = RouterSpec(routes=[make_route()])

        with pytest.raises(ValueError, match="classifier_prompt"):
            create_router_agent(spec, classifier=model_spec)

    def test_invalid_classifier_type_rejected(self, make_route: Callable[..., RouteSpec]) -> None:
        spec = RouterSpec(routes=[make_route()])

        with pytest.raises(TypeError, match="classifier"):
            create_router_agent(
                spec,
                classifier="not a model or callable",  # type: ignore[arg-type]
            )

    def test_empty_routes_rejected(self) -> None:
        with pytest.raises(ValueError, match="route"):
            create_router_agent(
                RouterSpec(routes=[]),
                classifier=lambda state: "x",
            )


class TestCallableClassifierBuildsGraph:
    def test_factory_compiles_with_callable_classifier(self) -> None:
        # End-to-end: a callable classifier + subgraph specialists
        # produces a compiled graph without touching any LLM.
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
                    target=SpecialistSpec(name="billing", subgraph=_make_passthrough("billing")),
                ),
            ],
        )

        graph = create_router_agent(spec, classifier=lambda state: "billing")

        # Compiled graph exists; that is what the test asserts.
        assert graph is not None


class TestLLMClassifierBuildsGraph:
    def test_llm_classifier_produces_compiled_graph(self, model_spec: ModelSpec) -> None:
        # Use a subgraph specialist so specialist_to_node does not call
        # create_react_agent (which emits a 1.0 deprecation warning that
        # the suite treats as error).
        billing_subgraph = MagicMock(name="compiled_subgraph")
        spec = RouterSpec(
            routes=[
                RouteSpec(
                    name="billing",
                    description="Billing handler.",
                    target=SpecialistSpec(name="billing", subgraph=billing_subgraph),
                )
            ],
        )

        with patch("langgraph_forge.builders.multiagent.router.get_model"):
            graph = create_router_agent(
                spec,
                classifier=model_spec,
                classifier_prompt="Pick the route that matches the request.",
            )

        assert graph is not None


class TestCompileForwarding:
    def test_compiled_with_spec_checkpointer(self, make_route: Callable[..., RouteSpec]) -> None:
        fake_checkpointer = MagicMock(spec=BaseCheckpointSaver)
        spec = RouterSpec(
            routes=[make_route()],
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

    def test_interrupts_pass_to_compile(self, make_route: Callable[..., RouteSpec]) -> None:
        spec = RouterSpec(
            routes=[make_route("billing"), make_route("tech")],
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


class TestStateSchemaForwarding:
    def test_default_state_schema_constructs_state_graph_with_router_state(
        self, make_route: Callable[..., RouteSpec]
    ) -> None:
        # When the user does not supply state_schema, the spec validator
        # fills RouterState; the factory must hand that to StateGraph.
        spec = RouterSpec(routes=[make_route()])
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

        mock_state_graph_class.assert_called_once_with(RouterState)

    def test_user_state_schema_subclass_constructs_state_graph_with_subclass(
        self, make_route: Callable[..., RouteSpec]
    ) -> None:
        # Mirrors swarm.py:50 -- a user-supplied subclass must reach
        # StateGraph untouched so the extra channels survive compile.
        class CustomRouterState(RouterState):
            risk_level: str

        spec = RouterSpec(routes=[make_route()], state_schema=CustomRouterState)
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

        mock_state_graph_class.assert_called_once_with(CustomRouterState)
