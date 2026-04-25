"""Tests for langgraph_forge.core.state.RouterState."""

from __future__ import annotations

import typing

from langgraph_forge.core.state import ForgeState, RouterState


class TestRouterStateShape:
    def test_inherits_messages_from_forge_state(self) -> None:
        assert "messages" in typing.get_type_hints(RouterState)

    def test_has_route_field(self) -> None:
        # The classifier writes `route`; the conditional edge reads it
        # to dispatch.
        assert "route" in typing.get_type_hints(RouterState)

    def test_extends_forge_state(self) -> None:
        orig_bases = getattr(RouterState, "__orig_bases__", ())
        assert ForgeState in orig_bases

    def test_instantiation_accepts_route(self) -> None:
        state: RouterState = {"messages": [], "route": "billing"}

        assert state["route"] == "billing"
