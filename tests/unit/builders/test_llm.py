"""Tests for langgraph_forge.builders.llm.get_model."""

from __future__ import annotations

from unittest.mock import patch

from langgraph_forge.builders.llm import get_model
from langgraph_forge.core.specs import ModelSpec


class TestGetModelDispatch:
    def test_forwards_model_and_provider(self) -> None:
        spec = ModelSpec(model="gpt-4o", provider="openai")
        with patch("langgraph_forge.builders.llm.init_chat_model") as mock_init:
            get_model(spec)

        mock_init.assert_called_once_with(
            model="gpt-4o",
            model_provider="openai",
            temperature=0.2,
        )

    def test_forwards_custom_temperature(self) -> None:
        spec = ModelSpec(model="claude-haiku-4-5", provider="anthropic", temperature=0.7)
        with patch("langgraph_forge.builders.llm.init_chat_model") as mock_init:
            get_model(spec)

        mock_init.assert_called_once_with(
            model="claude-haiku-4-5",
            model_provider="anthropic",
            temperature=0.7,
        )

    def test_spreads_extra_kwargs(self) -> None:
        spec = ModelSpec(
            model="gpt-4o",
            provider="openai",
            extra={"max_tokens": 4096, "top_p": 0.9},
        )
        with patch("langgraph_forge.builders.llm.init_chat_model") as mock_init:
            get_model(spec)

        mock_init.assert_called_once_with(
            model="gpt-4o",
            model_provider="openai",
            temperature=0.2,
            max_tokens=4096,
            top_p=0.9,
        )

    def test_returns_init_chat_model_result(self) -> None:
        spec = ModelSpec(model="gpt-4o", provider="openai")
        sentinel = object()
        with patch(
            "langgraph_forge.builders.llm.init_chat_model",
            return_value=sentinel,
        ):
            result = get_model(spec)

        assert result is sentinel
