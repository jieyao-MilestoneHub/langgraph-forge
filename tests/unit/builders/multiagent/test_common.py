"""Tests for langgraph_forge.builders.multiagent._common.specialist_to_node."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, sentinel

from langgraph_forge.builders.multiagent._common import specialist_to_node
from langgraph_forge.core.specs import ModelSpec, SpecialistSpec


def _react_spec(name: str = "researcher") -> SpecialistSpec:
    return SpecialistSpec(
        name=name,
        prompt="You are a researcher.",
        model=ModelSpec(model="gpt-4o", provider="openai"),
    )


class TestSpecialistToNodeReActMode:
    def test_react_specialist_built_via_create_react_agent(self) -> None:
        spec = _react_spec()
        with (
            patch(
                "langgraph_forge.builders.multiagent._common.create_react_agent",
                return_value=sentinel.worker,
            ) as mock_react,
            patch(
                "langgraph_forge.builders.multiagent._common.get_model",
                return_value=sentinel.chat_model,
            ),
        ):
            result = specialist_to_node(spec)

        assert result is sentinel.worker
        mock_react.assert_called_once_with(
            model=sentinel.chat_model,
            tools=spec.tools,
            prompt=spec.prompt,
            name=spec.name,
        )

    def test_react_specialist_uses_get_model_for_chat(self) -> None:
        # The helper must route through get_model so the spec -> chat-model
        # path stays singular; no specialist factory should call
        # init_chat_model directly.
        spec = _react_spec()
        with (
            patch("langgraph_forge.builders.multiagent._common.create_react_agent"),
            patch(
                "langgraph_forge.builders.multiagent._common.get_model"
            ) as mock_get,
        ):
            specialist_to_node(spec)

        mock_get.assert_called_once_with(spec.model)


class TestSpecialistToNodeSubgraphMode:
    def test_subgraph_returned_unchanged(self) -> None:
        # When a specialist is in subgraph mode, the helper hands back the
        # supplied compiled graph as-is. No wrapping, no re-compilation.
        fake_subgraph = MagicMock(name="compiled_subgraph")
        spec = SpecialistSpec(name="encoded_worker", subgraph=fake_subgraph)

        result = specialist_to_node(spec)

        assert result is fake_subgraph

    def test_subgraph_mode_does_not_call_create_react_agent(self) -> None:
        fake_subgraph = MagicMock(name="compiled_subgraph")
        spec = SpecialistSpec(name="encoded_worker", subgraph=fake_subgraph)

        with patch(
            "langgraph_forge.builders.multiagent._common.create_react_agent"
        ) as mock_react:
            specialist_to_node(spec)

        mock_react.assert_not_called()

    def test_subgraph_mode_does_not_call_get_model(self) -> None:
        # No LLM is constructed for an encoded-code specialist; the subgraph
        # carries its own behaviour.
        fake_subgraph = MagicMock(name="compiled_subgraph")
        spec = SpecialistSpec(name="encoded_worker", subgraph=fake_subgraph)

        with patch(
            "langgraph_forge.builders.multiagent._common.get_model"
        ) as mock_get:
            specialist_to_node(spec)

        mock_get.assert_not_called()
