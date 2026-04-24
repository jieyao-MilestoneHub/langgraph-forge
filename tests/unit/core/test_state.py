"""Tests for langgraph_forge.core.state."""

from __future__ import annotations

import typing

from langgraph.graph.message import add_messages

from langgraph_forge.core.state import ForgeState


class TestForgeStateShape:
    def test_has_messages_field(self) -> None:
        assert "messages" in ForgeState.__annotations__

    def test_messages_reducer_is_add_messages(self) -> None:
        # ForgeState.messages is Annotated[list, add_messages]; the reducer
        # sits in the annotation metadata returned by typing.get_args.
        annotation = ForgeState.__annotations__["messages"]
        metadata = typing.get_args(annotation)

        assert add_messages in metadata

    def test_instantiation_accepts_messages(self) -> None:
        # TypedDict is a dict at runtime; smoke-test a round-trip.
        state: ForgeState = {"messages": []}

        assert state["messages"] == []
