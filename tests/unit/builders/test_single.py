"""Tests for langgraph_forge.builders.single.create_single_agent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, sentinel

from langgraph_forge.builders.single import create_single_agent


class TestCreateSingleAgentDispatch:
    def test_forwards_model_tools_and_prompt(self) -> None:
        tool = MagicMock(name="stub_tool")
        with patch("langgraph_forge.builders.single.create_react_agent") as mock_create:
            create_single_agent(
                model=sentinel.model,
                tools=[tool],
                prompt="You are a helpful assistant.",
            )

        mock_create.assert_called_once_with(
            model=sentinel.model,
            tools=[tool],
            prompt="You are a helpful assistant.",
            checkpointer=None,
        )

    def test_prompt_defaults_to_none(self) -> None:
        with patch("langgraph_forge.builders.single.create_react_agent") as mock_create:
            create_single_agent(model=sentinel.model, tools=[])

        mock_create.assert_called_once_with(
            model=sentinel.model,
            tools=[],
            prompt=None,
            checkpointer=None,
        )

    def test_forwards_checkpointer(self) -> None:
        with patch("langgraph_forge.builders.single.create_react_agent") as mock_create:
            create_single_agent(
                model=sentinel.model,
                tools=[],
                checkpointer=sentinel.checkpointer,
            )

        mock_create.assert_called_once_with(
            model=sentinel.model,
            tools=[],
            prompt=None,
            checkpointer=sentinel.checkpointer,
        )

    def test_returns_create_react_agent_result(self) -> None:
        with patch(
            "langgraph_forge.builders.single.create_react_agent",
            return_value=sentinel.graph,
        ):
            result = create_single_agent(model=sentinel.model, tools=[])

        assert result is sentinel.graph
