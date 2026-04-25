"""Tests for langgraph_forge.core.specs.SpecialistSpec."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.tools import tool
from pydantic import ValidationError

from langgraph_forge.core.specs import ModelSpec, SpecialistSpec


def _model() -> ModelSpec:
    return ModelSpec(model="gpt-4o", provider="openai")


def _fake_subgraph() -> MagicMock:
    # CompiledStateGraph has too many internal moving parts to construct
    # cheaply in a unit test. A MagicMock with a reasonable repr is enough
    # for the validator -- the spec only checks that *something* was given.
    sub = MagicMock(name="compiled_subgraph")
    return sub


@tool
def _stub_tool(query: str) -> str:
    """Fixture tool: real BaseTool so Pydantic's type check passes."""
    return query


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
    def test_missing_both_react_and_subgraph_raises(self) -> None:
        # Name alone is insufficient -- the spec must declare an
        # encoding (either ReAct via prompt+model OR a subgraph).
        with pytest.raises(ValidationError, match=r"prompt.*model.*subgraph"):
            SpecialistSpec(name="researcher")

    def test_partial_react_missing_prompt_raises(self) -> None:
        # Only model, no prompt: incomplete ReAct mode and no subgraph.
        with pytest.raises(ValidationError, match=r"prompt.*model.*subgraph"):
            SpecialistSpec(name="researcher", model=_model())

    def test_partial_react_missing_model_raises(self) -> None:
        # Only prompt, no model: same incomplete-mode rejection.
        with pytest.raises(ValidationError, match=r"prompt.*model.*subgraph"):
            SpecialistSpec(name="researcher", prompt="p")

    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"extra_forbidden|Extra inputs"):
            SpecialistSpec(  # type: ignore[call-arg]
                name="researcher",
                prompt="p",
                model=_model(),
                nonexistent_field="oops",  # pyright: ignore[reportCallIssue]
            )


class TestSpecialistSpecSubgraphMode:
    def test_subgraph_alone_accepted(self) -> None:
        spec = SpecialistSpec(name="researcher", subgraph=_fake_subgraph())

        assert spec.subgraph is not None

    def test_subgraph_mode_has_no_prompt(self) -> None:
        spec = SpecialistSpec(name="researcher", subgraph=_fake_subgraph())

        assert spec.prompt is None

    def test_subgraph_mode_has_no_model(self) -> None:
        spec = SpecialistSpec(name="researcher", subgraph=_fake_subgraph())

        assert spec.model is None

    def test_subgraph_with_prompt_rejected(self) -> None:
        # Mixed mode -- a subgraph encapsulates its own prompts; supplying
        # a top-level prompt is ambiguous and almost always a mistake.
        with pytest.raises(ValidationError, match=r"subgraph.*prompt|prompt.*subgraph"):
            SpecialistSpec(
                name="researcher",
                prompt="p",
                subgraph=_fake_subgraph(),
            )

    def test_subgraph_with_model_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"subgraph.*model|model.*subgraph"):
            SpecialistSpec(
                name="researcher",
                model=_model(),
                subgraph=_fake_subgraph(),
            )

    def test_subgraph_with_tools_rejected(self) -> None:
        # Tools belong to a ReAct worker. A subgraph manages its own tools
        # internally; supplying tools at the spec level mixes the modes.
        with pytest.raises(ValidationError, match=r"subgraph.*tools|tools.*subgraph"):
            SpecialistSpec(
                name="researcher",
                tools=[_stub_tool],
                subgraph=_fake_subgraph(),
            )


class TestSpecialistSpecImmutability:
    def test_frozen_rejects_field_mutation(self) -> None:
        spec = SpecialistSpec(name="researcher", prompt="p", model=_model())

        with pytest.raises(ValidationError, match=r"frozen|immutable"):
            spec.name = "renamed"  # type: ignore[misc]
