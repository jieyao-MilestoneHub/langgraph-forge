"""Tests for langgraph_forge.builders.multiagent.hierarchical."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch, sentinel

import pytest
from langgraph.checkpoint.base import BaseCheckpointSaver

from langgraph_forge.builders.multiagent.hierarchical import (
    create_hierarchical_agent,
)
from langgraph_forge.core.specs import (
    ModelSpec,
    SpecialistSpec,
    TeamSpec,
)


@pytest.fixture(autouse=True)
def _mock_get_model() -> Iterator[MagicMock]:
    # The hierarchical factory calls get_model on each team's
    # supervisor_model. Without a real provider installed, init_chat_model
    # would fail. Auto-mock at the hierarchical module's import boundary
    # so every test in this file gets the same harmless stub.
    with patch(
        "langgraph_forge.builders.multiagent.hierarchical.get_model",
        return_value=sentinel.team_chat_model,
    ) as mock:
        yield mock


def _model() -> ModelSpec:
    return ModelSpec(model="gpt-4o", provider="openai")


def _team(name: str = "billing") -> TeamSpec:
    return TeamSpec(
        name=name,
        supervisor_model=_model(),
        supervisor_prompt=f"You manage the {name} team.",
        specialists=[
            SpecialistSpec(
                name=f"{name}_alpha", prompt="alpha", model=_model()
            ),
        ],
    )


class TestHierarchicalRecursivelyComposes:
    def test_one_create_supervisor_call_per_team_plus_one_for_top(self) -> None:
        teams = [_team("billing"), _team("tech_support")]
        # Mock the imported create_supervisor_agent so we count + inspect calls.
        with patch(
            "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
            return_value=sentinel.compiled,
        ) as mock_create:
            create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="You orchestrate teams.",
                teams=teams,
            )

        # 2 team supervisors + 1 top supervisor = 3 calls.
        assert mock_create.call_count == 3

    def test_each_team_supervisor_uses_team_specialists(self) -> None:
        teams = [_team("billing")]
        with (
            patch(
                "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
                return_value=sentinel.compiled,
            ) as mock_create,
            patch(
                "langgraph_forge.builders.multiagent.hierarchical.get_model",
                return_value=sentinel.team_chat_model,
            ),
        ):
            create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="p",
                teams=teams,
            )

        # First call is the team's supervisor; spec.specialists must be the
        # team's specialists.
        team_call_args, team_call_kwargs = mock_create.call_args_list[0]
        spec = team_call_args[0]
        assert spec.specialists == teams[0].specialists

    def test_each_team_supervisor_uses_team_model_and_prompt(self) -> None:
        team = _team("billing")
        with (
            patch(
                "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
                return_value=sentinel.compiled,
            ) as mock_create,
            patch(
                "langgraph_forge.builders.multiagent.hierarchical.get_model",
                return_value=sentinel.team_chat_model,
            ) as mock_get,
        ):
            create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="p",
                teams=[team],
            )

        # get_model is called for the team supervisor's ModelSpec.
        mock_get.assert_any_call(team.supervisor_model)

        # The inner create_supervisor_agent call gets the get_model output
        # plus the team's supervisor_prompt.
        team_call_args, team_call_kwargs = mock_create.call_args_list[0]
        assert team_call_kwargs["supervisor_model"] is sentinel.team_chat_model
        assert team_call_kwargs["supervisor_prompt"] == team.supervisor_prompt


class TestTopSupervisorReceivesTeamSubgraphs:
    def test_top_supervisor_gets_subgraph_specialists_named_after_teams(
        self,
    ) -> None:
        teams = [_team("billing"), _team("tech_support")]
        # Each call to inner create_supervisor_agent returns a different
        # sentinel so we can verify they propagate into the top
        # supervisor's specialists as subgraph references.
        team_compiled = [MagicMock(name="billing_compiled"), MagicMock(name="tech_compiled")]
        with patch(
            "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
            side_effect=[*team_compiled, sentinel.top_compiled],
        ) as mock_create:
            create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="p",
                teams=teams,
            )

        # Last call is the top supervisor; spec.specialists are the team
        # subgraphs wrapped in SpecialistSpec(name=team.name, subgraph=...).
        top_call_args, _ = mock_create.call_args_list[-1]
        top_spec = top_call_args[0]
        assert [s.name for s in top_spec.specialists] == ["billing", "tech_support"]
        assert [s.subgraph for s in top_spec.specialists] == team_compiled

    def test_top_supervisor_receives_top_model_and_prompt(self) -> None:
        with patch(
            "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
            return_value=sentinel.compiled,
        ) as mock_create:
            create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="orchestrate teams",
                teams=[_team()],
            )

        _, top_kwargs = mock_create.call_args_list[-1]
        assert top_kwargs["supervisor_model"] is sentinel.top_model
        assert top_kwargs["supervisor_prompt"] == "orchestrate teams"


class TestTopLevelCrossCuttingForwarding:
    def test_top_level_checkpointer_lands_on_top_spec(self) -> None:
        fake_checkpointer = MagicMock(spec=BaseCheckpointSaver)
        with patch(
            "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
            return_value=sentinel.compiled,
        ) as mock_create:
            create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="p",
                teams=[_team()],
                checkpointer=fake_checkpointer,
            )

        top_call_args, _ = mock_create.call_args_list[-1]
        top_spec = top_call_args[0]
        assert top_spec.checkpointer is fake_checkpointer

    def test_top_level_interrupts_land_on_top_spec(self) -> None:
        with patch(
            "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
            return_value=sentinel.compiled,
        ) as mock_create:
            create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="p",
                teams=[_team()],
                interrupt_before=("billing",),
                interrupt_after=("tech_support",),
            )

        top_call_args, _ = mock_create.call_args_list[-1]
        top_spec = top_call_args[0]
        assert top_spec.interrupt_before == ("billing",)
        assert top_spec.interrupt_after == ("tech_support",)

    def test_returns_top_supervisor_compiled_graph(self) -> None:
        with patch(
            "langgraph_forge.builders.multiagent.hierarchical.create_supervisor_agent",
            side_effect=[sentinel.team_compiled, sentinel.top_compiled],
        ):
            result = create_hierarchical_agent(
                top_supervisor_model=sentinel.top_model,
                top_supervisor_prompt="p",
                teams=[_team()],
            )

        assert result is sentinel.top_compiled
