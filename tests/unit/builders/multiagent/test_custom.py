"""Tests for langgraph_forge.builders.multiagent.custom."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from langgraph_forge.builders.multiagent.custom import create_custom_agent
from langgraph_forge.core.state import ForgeState


class TestEscapeHatchBuildsGraph:
    def test_state_graph_constructed_with_user_schema(self) -> None:
        # The user's state_schema must be the type we pass to StateGraph.
        mock_state_graph_class = MagicMock()
        mock_builder = MagicMock()
        mock_state_graph_class.return_value = mock_builder

        class MyState(ForgeState):
            pass

        def build(graph: StateGraph) -> None:
            return None

        with patch(
            "langgraph_forge.builders.multiagent.custom.StateGraph",
            mock_state_graph_class,
        ):
            create_custom_agent(state_schema=MyState, build=build)

        mock_state_graph_class.assert_called_once_with(MyState)

    def test_default_state_schema_is_forge_state(self) -> None:
        mock_state_graph_class = MagicMock()
        mock_builder = MagicMock()
        mock_state_graph_class.return_value = mock_builder

        def build(graph: StateGraph) -> None:
            return None

        with patch(
            "langgraph_forge.builders.multiagent.custom.StateGraph",
            mock_state_graph_class,
        ):
            create_custom_agent(build=build)

        mock_state_graph_class.assert_called_once_with(ForgeState)

    def test_real_compile_returns_runnable_graph(self) -> None:
        # End-to-end through the real StateGraph: a sequential planner
        # -> executor topology compiles and exposes invoke().
        def build(graph: StateGraph) -> None:
            graph.add_node("planner", lambda state: {"messages": []})
            graph.add_node("executor", lambda state: {"messages": []})
            graph.add_edge(START, "planner")
            graph.add_edge("planner", "executor")
            graph.add_edge("executor", END)

        graph = create_custom_agent(build=build)

        assert graph is not None
        assert hasattr(graph, "invoke")


class TestCrossCuttingForwarding:
    def test_checkpointer_passed_to_compile(self) -> None:
        fake_checkpointer = MagicMock(spec=BaseCheckpointSaver)
        mock_state_graph_class = MagicMock()
        mock_builder = MagicMock()
        mock_state_graph_class.return_value = mock_builder

        def build(graph: StateGraph) -> None:
            return None

        with patch(
            "langgraph_forge.builders.multiagent.custom.StateGraph",
            mock_state_graph_class,
        ):
            create_custom_agent(build=build, checkpointer=fake_checkpointer)

        _, kwargs = mock_builder.compile.call_args
        assert kwargs["checkpointer"] is fake_checkpointer

    def test_interrupts_passed_to_compile(self) -> None:
        mock_state_graph_class = MagicMock()
        mock_builder = MagicMock()
        mock_state_graph_class.return_value = mock_builder

        def build(graph: StateGraph) -> None:
            return None

        with patch(
            "langgraph_forge.builders.multiagent.custom.StateGraph",
            mock_state_graph_class,
        ):
            create_custom_agent(
                build=build,
                interrupt_before=("planner",),
                interrupt_after=("executor",),
            )

        _, kwargs = mock_builder.compile.call_args
        assert kwargs["interrupt_before"] == ["planner"]
        assert kwargs["interrupt_after"] == ["executor"]

    def test_build_callback_invoked_with_constructed_builder(self) -> None:
        # The build callback must receive the same StateGraph instance
        # that we later compile, so user nodes/edges land on the right
        # graph.
        mock_state_graph_class = MagicMock()
        mock_builder = MagicMock()
        mock_state_graph_class.return_value = mock_builder

        captured: list[object] = []

        def build(graph: StateGraph) -> None:
            captured.append(graph)

        with patch(
            "langgraph_forge.builders.multiagent.custom.StateGraph",
            mock_state_graph_class,
        ):
            create_custom_agent(build=build)

        assert captured == [mock_builder]
