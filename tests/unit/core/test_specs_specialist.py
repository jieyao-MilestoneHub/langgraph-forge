"""Tests for langgraph_forge.core.specs.SpecialistSpec."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from langgraph_forge.core.specs import ModelSpec, SpecialistSpec


def _model() -> ModelSpec:
    return ModelSpec(model="gpt-4o", provider="openai")


class TestSpecialistSpecHappyPath:
    def test_minimum_construction_succeeds(self) -> None:
        spec = SpecialistSpec(name="researcher", prompt="You are...", model=_model())

        assert spec.name == "researcher"

    def test_tools_default_empty_list(self) -> None:
        spec = SpecialistSpec(name="researcher", prompt="You are...", model=_model())

        assert spec.tools == []


class TestSpecialistSpecNamePattern:
    @pytest.mark.parametrize("name", ["a", "researcher", "agent_1", "x_y_z", "a" * 64])
    def test_valid_names_accepted(self, name: str) -> None:
        spec = SpecialistSpec(name=name, prompt="p", model=_model())

        assert spec.name == name

    @pytest.mark.parametrize(
        "name",
        [
            "",  # empty
            "1bad",  # digit start
            "Upper",  # uppercase
            "has space",  # whitespace
            "has-dash",  # dash not allowed
            "has.dot",  # dot not allowed
            "a" * 65,  # too long (>64)
        ],
    )
    def test_invalid_names_rejected(self, name: str) -> None:
        with pytest.raises(ValidationError, match="name"):
            SpecialistSpec(name=name, prompt="p", model=_model())


class TestSpecialistSpecValidation:
    def test_missing_prompt_raises(self) -> None:
        with pytest.raises(ValidationError, match="prompt"):
            SpecialistSpec(name="researcher", model=_model())  # type: ignore[call-arg]

    def test_missing_model_raises(self) -> None:
        with pytest.raises(ValidationError, match="model"):
            SpecialistSpec(name="researcher", prompt="p")  # type: ignore[call-arg]

    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"extra_forbidden|Extra inputs"):
            SpecialistSpec(  # type: ignore[call-arg]
                name="researcher",
                prompt="p",
                model=_model(),
                nonexistent_field="oops",  # pyright: ignore[reportCallIssue]
            )


class TestSpecialistSpecImmutability:
    def test_frozen_rejects_field_mutation(self) -> None:
        spec = SpecialistSpec(name="researcher", prompt="p", model=_model())

        with pytest.raises(ValidationError, match=r"frozen|immutable"):
            spec.name = "renamed"  # type: ignore[misc]
