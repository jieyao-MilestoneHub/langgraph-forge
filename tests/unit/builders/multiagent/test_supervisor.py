"""Tests for langgraph_forge.builders.multiagent.supervisor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, sentinel

from langgraph.checkpoint.base import BaseCheckpointSaver

from langgraph_forge.builders.multiagent.supervisor import create_supervisor_agent
from langgraph_forge.core.specs import (
    ModelSpec,
    MultiAgentSpec,
    SpecialistSpec,
)


def _spec(name: str = "alpha") -> SpecialistSpec:
    return SpecialistSpec(
        name=name,
        prompt=f"You are {name}.",
        model=ModelSpec(model="gpt-4o", provider="openai"),
    )


class TestCreateSupervisorAgentComposition:
    def test_each_specialist_routed_through_specialist_to_node(self) -> None:
        # The supervisor delegates worker construction to _common.
        # We verify both calls happen rather than re-testing specialist_to_node.
        spec = MultiAgentSpec(specialists=[_spec("a"), _spec("b")])
        with (
            patch("langgraph_forge.builders.multiagent.supervisor.specialist_to_node") as mock_node,
            patch("langgraph_forge.builders.multiagent.supervisor.create_supervisor"),
        ):
            create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="orchestrate",
            )

        assert mock_node.call_count == 2

    def test_workers_passed_to_create_supervisor(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec("a"), _spec("b")])
        workers = [sentinel.worker_a, sentinel.worker_b]
        with (
            patch(
                "langgraph_forge.builders.multiagent.supervisor.specialist_to_node",
                side_effect=workers,
            ),
            patch("langgraph_forge.builders.multiagent.supervisor.create_supervisor") as mock_sup,
        ):
            create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="orchestrate",
            )

        _, kwargs = mock_sup.call_args
        assert kwargs["agents"] == workers

    def test_supervisor_model_and_prompt_forwarded(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()])
        with (
            patch("langgraph_forge.builders.multiagent.supervisor.specialist_to_node"),
            patch("langgraph_forge.builders.multiagent.supervisor.create_supervisor") as mock_sup,
        ):
            create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="custom prompt",
            )

        _, kwargs = mock_sup.call_args
        assert (kwargs["model"], kwargs["prompt"]) == (
            sentinel.supervisor_model,
            "custom prompt",
        )


class TestCompileWiring:
    def test_compiled_with_spec_checkpointer(self) -> None:
        # MultiAgentSpec.checkpointer is typed BaseCheckpointSaver | None,
        # so sentinel objects fail Pydantic validation. spec= the mock to
        # the real type so isinstance / pydantic accept it.
        fake_checkpointer = MagicMock(spec=BaseCheckpointSaver)
        spec = MultiAgentSpec(
            specialists=[_spec()],
            checkpointer=fake_checkpointer,
        )
        sup_graph = MagicMock(name="supervisor_graph")
        with (
            patch("langgraph_forge.builders.multiagent.supervisor.specialist_to_node"),
            patch(
                "langgraph_forge.builders.multiagent.supervisor.create_supervisor",
                return_value=sup_graph,
            ),
        ):
            create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="p",
            )

        # checkpointer is the only required compile() kwarg here; interrupts
        # land in the dedicated tests below.
        _, kwargs = sup_graph.compile.call_args
        assert kwargs["checkpointer"] is fake_checkpointer

    def test_interrupt_before_passed_to_compile(self) -> None:
        spec = MultiAgentSpec(
            specialists=[_spec()],
            interrupt_before=("alpha",),
        )
        sup_graph = MagicMock()
        with (
            patch("langgraph_forge.builders.multiagent.supervisor.specialist_to_node"),
            patch(
                "langgraph_forge.builders.multiagent.supervisor.create_supervisor",
                return_value=sup_graph,
            ),
        ):
            create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="p",
            )

        _, kwargs = sup_graph.compile.call_args
        # spec stores tuples for immutability; supervisor converts to list
        # at the compile() boundary because upstream's signature requires
        # list[str] | None. Test asserts the post-conversion shape.
        assert kwargs["interrupt_before"] == ["alpha"]

    def test_interrupt_after_passed_to_compile(self) -> None:
        spec = MultiAgentSpec(
            specialists=[_spec()],
            interrupt_after=("alpha",),
        )
        sup_graph = MagicMock()
        with (
            patch("langgraph_forge.builders.multiagent.supervisor.specialist_to_node"),
            patch(
                "langgraph_forge.builders.multiagent.supervisor.create_supervisor",
                return_value=sup_graph,
            ),
        ):
            create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="p",
            )

        _, kwargs = sup_graph.compile.call_args
        assert kwargs["interrupt_after"] == ["alpha"]

    def test_returns_compiled_graph(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()])
        sup_graph = MagicMock()
        sup_graph.compile.return_value = sentinel.compiled
        with (
            patch("langgraph_forge.builders.multiagent.supervisor.specialist_to_node"),
            patch(
                "langgraph_forge.builders.multiagent.supervisor.create_supervisor",
                return_value=sup_graph,
            ),
        ):
            result = create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="p",
            )

        assert result is sentinel.compiled


class TestSubgraphSpecialistAccepted:
    def test_subgraph_specialist_routed_through_specialist_to_node(self) -> None:
        # A specialist in subgraph mode lands in the supervisor's worker
        # list via specialist_to_node, which returns the subgraph
        # unchanged. The supervisor neither inspects nor recompiles it.
        fake_subgraph = MagicMock(name="compiled_subgraph")
        spec = MultiAgentSpec(
            specialists=[
                SpecialistSpec(name="encoded", subgraph=fake_subgraph),
            ]
        )
        with (
            patch(
                "langgraph_forge.builders.multiagent.supervisor.specialist_to_node",
                return_value=fake_subgraph,
            ),
            patch("langgraph_forge.builders.multiagent.supervisor.create_supervisor") as mock_sup,
        ):
            create_supervisor_agent(
                spec,
                supervisor_model=sentinel.supervisor_model,
                supervisor_prompt="p",
            )

        _, kwargs = mock_sup.call_args
        assert kwargs["agents"] == [fake_subgraph]
