"""Tests for langgraph_forge.core.specs.ModelSpec."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from langgraph_forge.core.specs import ModelSpec


class TestModelSpecHappyPath:
    def test_minimum_construction_succeeds(self) -> None:
        spec = ModelSpec(model="gpt-4o", provider="openai")

        assert spec.model == "gpt-4o"

    def test_default_temperature_is_02(self) -> None:
        spec = ModelSpec(model="gpt-4o", provider="openai")

        assert spec.temperature == 0.2

    def test_default_extra_is_empty_dict(self) -> None:
        spec = ModelSpec(model="gpt-4o", provider="openai")

        assert spec.extra == {}

    def test_extra_passthrough_preserved(self) -> None:
        spec = ModelSpec(
            model="claude-haiku-4-5",
            provider="anthropic",
            extra={"max_tokens": 4096},
        )

        assert spec.extra == {"max_tokens": 4096}


class TestModelSpecValidation:
    def test_missing_model_raises(self) -> None:
        with pytest.raises(ValidationError, match="model"):
            ModelSpec(provider="openai")  # type: ignore[call-arg]

    def test_missing_provider_raises(self) -> None:
        with pytest.raises(ValidationError, match="provider"):
            ModelSpec(model="gpt-4o")  # type: ignore[call-arg]

    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden|Extra inputs"):
            ModelSpec(  # type: ignore[call-arg]
                model="gpt-4o",
                provider="openai",
                nonexistent_field="oops",
            )


class TestModelSpecImmutability:
    def test_frozen_rejects_field_mutation(self) -> None:
        spec = ModelSpec(model="gpt-4o", provider="openai")

        with pytest.raises(ValidationError, match="frozen|immutable"):
            spec.model = "gpt-4-turbo"  # type: ignore[misc]
