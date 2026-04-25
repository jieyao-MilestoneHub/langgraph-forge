"""Tests for langgraph_forge.core.specs.TeamSpec."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from langgraph_forge.core.specs import ModelSpec, SpecialistSpec, TeamSpec


def _model() -> ModelSpec:
    return ModelSpec(model="gpt-4o", provider="openai")


def _specialist(name: str = "alpha") -> SpecialistSpec:
    return SpecialistSpec(name=name, prompt="p", model=_model())


class TestTeamSpecConstruction:
    def test_minimum_construction(self) -> None:
        team = TeamSpec(
            name="billing",
            supervisor_model=_model(),
            supervisor_prompt="Resolve billing issues.",
            specialists=[_specialist()],
        )

        assert team.name == "billing"

    def test_specialists_required(self) -> None:
        with pytest.raises(ValidationError, match="specialists"):
            TeamSpec(  # type: ignore[call-arg]
                name="billing",
                supervisor_model=_model(),
                supervisor_prompt="p",
            )

    def test_supervisor_prompt_required(self) -> None:
        with pytest.raises(ValidationError, match="supervisor_prompt"):
            TeamSpec(  # type: ignore[call-arg]
                name="billing",
                supervisor_model=_model(),
                specialists=[_specialist()],
            )


class TestTeamSpecNamePattern:
    @pytest.mark.parametrize(
        "name", ["a", "billing", "tech_support", "team_1"]
    )
    def test_valid_names_accepted(self, name: str) -> None:
        team = TeamSpec(
            name=name,
            supervisor_model=_model(),
            supervisor_prompt="p",
            specialists=[_specialist()],
        )

        assert team.name == name

    @pytest.mark.parametrize(
        "name", ["", "1invalid", "Has-Dash", "has space"]
    )
    def test_invalid_names_rejected(self, name: str) -> None:
        with pytest.raises(ValidationError, match="name"):
            TeamSpec(
                name=name,
                supervisor_model=_model(),
                supervisor_prompt="p",
                specialists=[_specialist()],
            )


class TestTeamSpecImmutability:
    def test_frozen_rejects_mutation(self) -> None:
        team = TeamSpec(
            name="billing",
            supervisor_model=_model(),
            supervisor_prompt="p",
            specialists=[_specialist()],
        )

        with pytest.raises(ValidationError, match=r"frozen|immutable"):
            team.name = "renamed"  # type: ignore[misc]

    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"extra_forbidden|Extra inputs"):
            TeamSpec(  # type: ignore[call-arg]
                name="billing",
                supervisor_model=_model(),
                supervisor_prompt="p",
                specialists=[_specialist()],
                nonexistent="oops",  # pyright: ignore[reportCallIssue]
            )
