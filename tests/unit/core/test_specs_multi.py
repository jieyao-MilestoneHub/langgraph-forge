"""Tests for langgraph_forge.core.specs.MultiAgentSpec."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from langgraph_forge.core.specs import (
    ModelSpec,
    MultiAgentSpec,
    SpecialistSpec,
)
from langgraph_forge.core.state import ForgeState


def _spec(name: str = "alpha") -> SpecialistSpec:
    return SpecialistSpec(name=name, prompt="p", model=ModelSpec(model="gpt-4o", provider="openai"))


class TestMultiAgentSpecConstruction:
    def test_specialists_required(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec("a"), _spec("b")])

        assert len(spec.specialists) == 2

    def test_state_schema_defaults_to_forge_state(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()])

        assert spec.state_schema is ForgeState

    def test_checkpointer_defaults_to_none(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()])

        assert spec.checkpointer is None

    def test_interrupt_before_defaults_to_empty_tuple(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()])

        assert spec.interrupt_before == ()

    def test_interrupt_after_defaults_to_empty_tuple(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()])

        assert spec.interrupt_after == ()


class TestMultiAgentSpecImmutability:
    def test_frozen_rejects_field_mutation(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()])

        with pytest.raises(ValidationError, match=r"frozen|immutable"):
            spec.specialists = []  # type: ignore[misc]


class TestMultiAgentSpecValidation:
    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"extra_forbidden|Extra inputs"):
            MultiAgentSpec(  # type: ignore[call-arg]
                specialists=[_spec()],
                nonexistent_field="oops",  # pyright: ignore[reportCallIssue]
            )

    def test_user_state_subclass_accepted(self) -> None:
        # Users extend ForgeState with their own channels; the spec should
        # accept any subclass without touching the runtime types.
        class MyState(ForgeState):
            extra: str

        spec = MultiAgentSpec(specialists=[_spec()], state_schema=MyState)

        assert spec.state_schema is MyState


class TestMultiAgentSpecInterruptDeclarations:
    def test_interrupt_before_round_trips_node_names(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()], interrupt_before=("research",))

        assert spec.interrupt_before == ("research",)

    def test_interrupt_after_round_trips_node_names(self) -> None:
        spec = MultiAgentSpec(specialists=[_spec()], interrupt_after=("billing",))

        assert spec.interrupt_after == ("billing",)
