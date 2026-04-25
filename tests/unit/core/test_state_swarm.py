"""Tests for langgraph_forge.core.state.SwarmState."""

from __future__ import annotations

import typing

from langgraph_forge.core.state import ForgeState, SwarmState


class TestSwarmStateShape:
    def test_inherits_messages_from_forge_state(self) -> None:
        # SwarmState extends ForgeState so users keep the messages
        # channel and can subclass either as a starting point.
        assert "messages" in typing.get_type_hints(SwarmState)

    def test_has_active_agent_field(self) -> None:
        # active_agent is what swarm patterns route on; it is updated
        # by handoff tools as agents transfer control to peers.
        assert "active_agent" in typing.get_type_hints(SwarmState)

    def test_swarm_state_extends_forge_state(self) -> None:
        # TypedDict subclasses at runtime are all `dict`, so issubclass
        # is not the right check. __orig_bases__ records the declared
        # parent and persists the boundary doc's "extend the base, don't
        # replace it" idiom for swarm users.
        assert ForgeState in SwarmState.__orig_bases__

    def test_instantiation_accepts_active_agent(self) -> None:
        # TypedDict at runtime is just a dict; smoke-test the round trip.
        state: SwarmState = {"messages": [], "active_agent": "alice"}

        assert state["active_agent"] == "alice"
