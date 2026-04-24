"""Tests for langgraph_forge.builders.supervisor.create_supervisor_agent."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, sentinel

from langgraph_forge.builders.supervisor import create_supervisor_agent
from langgraph_forge.core.specs import ModelSpec, SpecialistSpec


def _spec(name: str) -> SpecialistSpec:
    return SpecialistSpec(
        name=name,
        prompt=f"You are {name}.",
        model=ModelSpec(model="gpt-4o", provider="openai"),
    )


class TestCreateSupervisorAgentComposition:
    def test_each_specialist_becomes_a_react_worker(self) -> None:
        specs = [_spec("researcher"), _spec("summariser")]
        workers = [sentinel.worker_a, sentinel.worker_b]

        with (
            patch(
                "langgraph_forge.builders.supervisor.create_react_agent",
                side_effect=workers,
            ) as mock_react,
            patch("langgraph_forge.builders.supervisor.create_supervisor"),
            patch(
                "langgraph_forge.builders.supervisor.get_model",
                return_value=sentinel.worker_model,
            ),
        ):
            create_supervisor_agent(
                supervisor_model=sentinel.supervisor_model,
                specialists=specs,
                supervisor_prompt="You orchestrate.",
            )

        assert mock_react.call_count == 2

    def test_workers_are_passed_to_create_supervisor(self) -> None:
        specs = [_spec("researcher")]
        worker = MagicMock(name="worker")

        with (
            patch(
                "langgraph_forge.builders.supervisor.create_react_agent",
                return_value=worker,
            ),
            patch(
                "langgraph_forge.builders.supervisor.create_supervisor",
            ) as mock_sup,
            patch("langgraph_forge.builders.supervisor.get_model"),
        ):
            create_supervisor_agent(
                supervisor_model=sentinel.supervisor_model,
                specialists=specs,
                supervisor_prompt="orchestrate",
            )

        _, kwargs = mock_sup.call_args
        assert kwargs["agents"] == [worker]

    def test_supervisor_model_and_prompt_forwarded(self) -> None:
        with (
            patch("langgraph_forge.builders.supervisor.create_react_agent"),
            patch(
                "langgraph_forge.builders.supervisor.create_supervisor",
            ) as mock_sup,
            patch("langgraph_forge.builders.supervisor.get_model"),
        ):
            create_supervisor_agent(
                supervisor_model=sentinel.supervisor_model,
                specialists=[_spec("researcher")],
                supervisor_prompt="custom prompt",
            )

        _, kwargs = mock_sup.call_args
        assert (kwargs["model"], kwargs["prompt"]) == (
            sentinel.supervisor_model,
            "custom prompt",
        )

    def test_compiled_with_checkpointer(self) -> None:
        sup_graph = MagicMock(name="supervisor_graph")

        with (
            patch("langgraph_forge.builders.supervisor.create_react_agent"),
            patch(
                "langgraph_forge.builders.supervisor.create_supervisor",
                return_value=sup_graph,
            ),
            patch("langgraph_forge.builders.supervisor.get_model"),
        ):
            create_supervisor_agent(
                supervisor_model=sentinel.supervisor_model,
                specialists=[_spec("r")],
                supervisor_prompt="p",
                checkpointer=sentinel.checkpointer,
            )

        sup_graph.compile.assert_called_once_with(checkpointer=sentinel.checkpointer)


class TestWorkerArgsFromSpec:
    def test_worker_name_matches_spec_name(self) -> None:
        with (
            patch(
                "langgraph_forge.builders.supervisor.create_react_agent",
            ) as mock_react,
            patch("langgraph_forge.builders.supervisor.create_supervisor"),
            patch("langgraph_forge.builders.supervisor.get_model"),
        ):
            create_supervisor_agent(
                supervisor_model=sentinel.supervisor_model,
                specialists=[_spec("alpha")],
                supervisor_prompt="p",
            )

        _, kwargs = mock_react.call_args
        assert kwargs["name"] == "alpha"

    def test_worker_prompt_matches_spec_prompt(self) -> None:
        with (
            patch(
                "langgraph_forge.builders.supervisor.create_react_agent",
            ) as mock_react,
            patch("langgraph_forge.builders.supervisor.create_supervisor"),
            patch("langgraph_forge.builders.supervisor.get_model"),
        ):
            create_supervisor_agent(
                supervisor_model=sentinel.supervisor_model,
                specialists=[_spec("alpha")],
                supervisor_prompt="p",
            )

        _, kwargs = mock_react.call_args
        assert kwargs["prompt"] == "You are alpha."

    def test_worker_model_obtained_via_get_model(self) -> None:
        spec = _spec("alpha")
        with (
            patch("langgraph_forge.builders.supervisor.create_react_agent"),
            patch("langgraph_forge.builders.supervisor.create_supervisor"),
            patch("langgraph_forge.builders.supervisor.get_model") as mock_get,
        ):
            create_supervisor_agent(
                supervisor_model=sentinel.supervisor_model,
                specialists=[spec],
                supervisor_prompt="p",
            )

        mock_get.assert_called_once_with(spec.model)
