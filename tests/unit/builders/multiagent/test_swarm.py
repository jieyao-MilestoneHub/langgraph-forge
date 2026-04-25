"""Tests for langgraph_forge.builders.multiagent.swarm."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, sentinel

from langgraph.checkpoint.base import BaseCheckpointSaver

from langgraph_forge.builders.multiagent.swarm import create_swarm_agent
from langgraph_forge.core.specs import (
    ModelSpec,
    MultiAgentSpec,
    SpecialistSpec,
)
from langgraph_forge.core.state import ForgeState, SwarmState


def _spec(name: str = "alpha") -> SpecialistSpec:
    return SpecialistSpec(
        name=name,
        prompt=f"You are {name}.",
        model=ModelSpec(model="gpt-4o", provider="openai"),
    )


class TestCreateSwarmAgentComposition:
    def test_each_specialist_routed_through_specialist_to_node(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec("a"), _spec("b")])
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node") as mock_node,
            patch("langgraph_forge.builders.multiagent.swarm.create_swarm"),
        ):
            create_swarm_agent(spec, default_active_agent="a")

        assert mock_node.call_count == 2

    def test_workers_passed_to_create_swarm(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec("a"), _spec("b")])
        workers = [sentinel.worker_a, sentinel.worker_b]
        with (
            patch(
                "langgraph_forge.builders.multiagent.swarm.specialist_to_node",
                side_effect=workers,
            ),
            patch("langgraph_forge.builders.multiagent.swarm.create_swarm") as mock_swarm,
        ):
            create_swarm_agent(spec, default_active_agent="a")

        _, kwargs = mock_swarm.call_args
        assert kwargs["agents"] == workers

    def test_default_active_agent_forwarded(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec("a")])
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node"),
            patch("langgraph_forge.builders.multiagent.swarm.create_swarm") as mock_swarm,
        ):
            create_swarm_agent(spec, default_active_agent="a")

        _, kwargs = mock_swarm.call_args
        assert kwargs["default_active_agent"] == "a"


class TestStateSchemaDispatch:
    def test_default_forge_state_swapped_to_swarm_state(self) -> None:
        # Swarm needs `active_agent` -- if user did not customise state,
        # the factory swaps the default ForgeState for SwarmState rather
        # than failing at runtime.
        spec = MultiAgentSpec(specialists=[_spec("a")])
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node"),
            patch("langgraph_forge.builders.multiagent.swarm.create_swarm") as mock_swarm,
        ):
            create_swarm_agent(spec, default_active_agent="a")

        _, kwargs = mock_swarm.call_args
        assert kwargs["state_schema"] is SwarmState

    def test_user_state_subclass_honoured(self) -> None:
        # If the user already extended SwarmState (or provided their own
        # schema with active_agent), the factory does not override it.
        class MyState(SwarmState):
            scratchpad: str

        spec = MultiAgentSpec(
            specialists=[_spec("a")],
            state_schema=MyState,
        )
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node"),
            patch("langgraph_forge.builders.multiagent.swarm.create_swarm") as mock_swarm,
        ):
            create_swarm_agent(spec, default_active_agent="a")

        _, kwargs = mock_swarm.call_args
        assert kwargs["state_schema"] is MyState

    def test_only_exact_forge_state_is_replaced(self) -> None:
        # If a user passed a ForgeState subclass that is NOT SwarmState,
        # respect their decision (they may not need active_agent for
        # whatever they are building -- though swarm semantics will then
        # break at runtime; that is their explicit choice).
        class CustomBase(ForgeState):
            note: str

        spec = MultiAgentSpec(
            specialists=[_spec("a")],
            state_schema=CustomBase,
        )
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node"),
            patch("langgraph_forge.builders.multiagent.swarm.create_swarm") as mock_swarm,
        ):
            create_swarm_agent(spec, default_active_agent="a")

        _, kwargs = mock_swarm.call_args
        assert kwargs["state_schema"] is CustomBase


class TestCompileWiring:
    def test_compiled_with_spec_checkpointer(self) -> None:
        fake_checkpointer = MagicMock(spec=BaseCheckpointSaver)
        spec = MultiAgentSpec(
            specialists=[_spec("a")],
            checkpointer=fake_checkpointer,
        )
        workflow = MagicMock()
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node"),
            patch(
                "langgraph_forge.builders.multiagent.swarm.create_swarm",
                return_value=workflow,
            ),
        ):
            create_swarm_agent(spec, default_active_agent="a")

        _, kwargs = workflow.compile.call_args
        assert kwargs["checkpointer"] is fake_checkpointer

    def test_interrupt_before_passed_to_compile(self) -> None:
        spec = MultiAgentSpec(
            specialists=[_spec("a")],
            interrupt_before=("a",),
        )
        workflow = MagicMock()
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node"),
            patch(
                "langgraph_forge.builders.multiagent.swarm.create_swarm",
                return_value=workflow,
            ),
        ):
            create_swarm_agent(spec, default_active_agent="a")

        _, kwargs = workflow.compile.call_args
        assert kwargs["interrupt_before"] == ["a"]

    def test_returns_compiled_graph(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec("a")])
        workflow = MagicMock()
        workflow.compile.return_value = sentinel.compiled
        with (
            patch("langgraph_forge.builders.multiagent.swarm.specialist_to_node"),
            patch(
                "langgraph_forge.builders.multiagent.swarm.create_swarm",
                return_value=workflow,
            ),
        ):
            result = create_swarm_agent(spec, default_active_agent="a")

        assert result is sentinel.compiled
