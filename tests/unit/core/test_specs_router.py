"""Tests for RouteSpec / RouterSpec in langgraph_forge.core.specs."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from langgraph_forge.core.specs import (
    ModelSpec,
    RouterSpec,
    RouteSpec,
    SpecialistSpec,
)
from langgraph_forge.core.state import RouterState


def _model() -> ModelSpec:
    return ModelSpec(model="gpt-4o", provider="openai")


def _specialist(name: str = "alpha") -> SpecialistSpec:
    return SpecialistSpec(name=name, prompt="p", model=_model())


class TestRouteSpec:
    def test_minimum_construction(self) -> None:
        route = RouteSpec(
            name="billing",
            description="Billing, invoices, and refunds.",
            target=_specialist("billing_handler"),
        )

        assert route.name == "billing"

    def test_description_required(self) -> None:
        with pytest.raises(ValidationError, match="description"):
            RouteSpec(  # type: ignore[call-arg]
                name="billing",
                target=_specialist(),
            )

    def test_target_required(self) -> None:
        with pytest.raises(ValidationError, match="target"):
            RouteSpec(  # type: ignore[call-arg]
                name="billing",
                description="...",
            )

    @pytest.mark.parametrize("bad_name", ["", "1invalid", "Has-Dash", "has space"])
    def test_invalid_route_name_rejected(self, bad_name: str) -> None:
        with pytest.raises(ValidationError, match="name"):
            RouteSpec(
                name=bad_name,
                description="d",
                target=_specialist(),
            )

    def test_frozen(self) -> None:
        route = RouteSpec(name="billing", description="d", target=_specialist())

        with pytest.raises(ValidationError, match=r"frozen|immutable"):
            route.name = "renamed"  # type: ignore[misc]


class TestRouterSpec:
    def test_minimum_construction(self) -> None:
        spec = RouterSpec(
            routes=[
                RouteSpec(name="billing", description="d", target=_specialist("a")),
            ],
        )

        assert len(spec.routes) == 1

    def test_default_route_defaults_to_none(self) -> None:
        spec = RouterSpec(
            routes=[
                RouteSpec(name="billing", description="d", target=_specialist("a")),
            ],
        )

        assert spec.default_route is None

    def test_default_route_can_be_set(self) -> None:
        spec = RouterSpec(
            routes=[
                RouteSpec(name="billing", description="d", target=_specialist("a")),
            ],
            default_route="billing",
        )

        assert spec.default_route == "billing"

    def test_frozen(self) -> None:
        spec = RouterSpec(
            routes=[
                RouteSpec(name="billing", description="d", target=_specialist("a")),
            ],
        )

        with pytest.raises(ValidationError, match=r"frozen|immutable"):
            spec.routes = []  # type: ignore[misc]

    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(ValidationError, match=r"extra_forbidden|Extra inputs"):
            RouterSpec(  # type: ignore[call-arg]
                routes=[
                    RouteSpec(name="billing", description="d", target=_specialist("a")),
                ],
                nonexistent="oops",  # pyright: ignore[reportCallIssue]
            )


class TestRouterSpecStateSchema:
    def test_state_schema_defaults_to_router_state(self) -> None:
        # Mirrors MultiAgentSpec's auto-default to ForgeState; lets the
        # router factory honour subclasses while keeping the common case
        # zero-config.
        spec = RouterSpec(
            routes=[
                RouteSpec(name="billing", description="d", target=_specialist("a")),
            ],
        )

        assert spec.state_schema is RouterState

    def test_user_supplied_state_schema_subclass_preserved(self) -> None:
        class CustomRouterState(RouterState):
            risk_level: str

        spec = RouterSpec(
            routes=[
                RouteSpec(name="billing", description="d", target=_specialist("a")),
            ],
            state_schema=CustomRouterState,
        )

        assert spec.state_schema is CustomRouterState
