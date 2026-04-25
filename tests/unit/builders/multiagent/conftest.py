"""Shared fixtures for multi-agent builder tests.

Every test in this directory needs a ``ModelSpec`` for SpecialistSpec
construction; tests that exercise specialist-to-node conversion or
hierarchical recursion also need ``get_model`` mocked at the right
import boundary so ``init_chat_model`` is never called for real.

Both concerns live here rather than in each test file:
- **Helper factories** -- ``model_spec``, ``make_specialist``,
  ``make_route``, ``make_team`` -- so a domain change to the canonical
  test ModelSpec or SpecialistSpec shape touches one file.
- **Autouse get_model mock** -- patches both ``_common.get_model`` and
  ``hierarchical.get_model`` so every multi-agent test runs without a
  real provider, regardless of which factory's import path it
  exercises.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from unittest.mock import MagicMock, patch

import pytest

from langgraph_forge.core.specs import (
    ModelSpec,
    RouteSpec,
    SpecialistSpec,
    TeamSpec,
)


@pytest.fixture(autouse=True)
def _mock_get_model() -> Iterator[None]:
    """Mock get_model wherever a multi-agent factory imports it.

    Tests that exercise create_supervisor / create_swarm /
    create_router / create_hierarchical may end up calling get_model
    via either ``_common.specialist_to_node`` (ReAct specialists) or
    via the hierarchical factory's own import (team supervisors).
    Without a real provider in the dev env, ``init_chat_model`` would
    fail. Patch both boundaries here so individual tests stay focused
    on the wiring they care about.
    """
    with (
        patch(
            "langgraph_forge.builders.multiagent._common.get_model",
            return_value=MagicMock(),
        ),
        patch(
            "langgraph_forge.builders.multiagent.hierarchical.get_model",
            return_value=MagicMock(),
        ),
    ):
        yield


@pytest.fixture
def model_spec() -> ModelSpec:
    """Canonical ModelSpec used across multi-agent tests."""
    return ModelSpec(model="gpt-4o", provider="openai")


@pytest.fixture
def make_specialist(model_spec: ModelSpec) -> Callable[..., SpecialistSpec]:
    """Factory: SpecialistSpec with a sensible default prompt and ModelSpec."""

    def _make(name: str = "alpha", prompt: str = "p") -> SpecialistSpec:
        return SpecialistSpec(name=name, prompt=prompt, model=model_spec)

    return _make


@pytest.fixture
def make_route(make_specialist: Callable[..., SpecialistSpec]) -> Callable[..., RouteSpec]:
    """Factory: RouteSpec wrapping a default ReAct specialist target."""

    def _make(name: str = "billing") -> RouteSpec:
        return RouteSpec(
            name=name,
            description=f"Handles {name} requests.",
            target=make_specialist(f"{name}_handler"),
        )

    return _make


@pytest.fixture
def make_team(
    model_spec: ModelSpec,
    make_specialist: Callable[..., SpecialistSpec],
) -> Callable[..., TeamSpec]:
    """Factory: TeamSpec with one default specialist and the canonical model."""

    def _make(name: str = "billing") -> TeamSpec:
        return TeamSpec(
            name=name,
            supervisor_model=model_spec,
            supervisor_prompt=f"You manage the {name} team.",
            specialists=[make_specialist(f"{name}_alpha", prompt="alpha")],
        )

    return _make
