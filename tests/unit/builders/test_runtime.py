"""Tests for langgraph_forge.builders.runtime: replay (resume dropped in 0.3.0a1)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from langgraph_forge.builders.runtime import replay
from langgraph_forge.core.specs import ThreadConfig


class TestReplay:
    @pytest.mark.asyncio
    async def test_calls_ainvoke_with_none_and_config(self) -> None:
        graph = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"messages": ["ok"]})
        thread = ThreadConfig(thread_id="run-42", checkpoint_id="ckpt-7")

        await replay(graph, thread)

        graph.ainvoke.assert_awaited_once_with(None, thread.to_langgraph())

    @pytest.mark.asyncio
    async def test_returns_ainvoke_result(self) -> None:
        graph = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"messages": ["resumed"]})
        thread = ThreadConfig(thread_id="run-42")

        result = await replay(graph, thread)

        assert result == {"messages": ["resumed"]}

    @pytest.mark.asyncio
    async def test_modify_updates_state_before_invoke(self) -> None:
        graph = MagicMock()
        graph.ainvoke = AsyncMock(return_value={})
        graph.aupdate_state = AsyncMock()
        thread = ThreadConfig(thread_id="run-42", checkpoint_id="ckpt-7")
        modify = {"counter": 5}

        await replay(graph, thread, modify=modify)

        graph.aupdate_state.assert_awaited_once_with(thread.to_langgraph(), modify)

    @pytest.mark.asyncio
    async def test_no_modify_skips_update_state(self) -> None:
        graph = MagicMock()
        graph.ainvoke = AsyncMock(return_value={})
        graph.aupdate_state = AsyncMock()
        thread = ThreadConfig(thread_id="run-42")

        await replay(graph, thread)

        graph.aupdate_state.assert_not_awaited()
