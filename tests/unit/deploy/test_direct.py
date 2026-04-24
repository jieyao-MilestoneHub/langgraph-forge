"""Tests for langgraph_forge.deploy.direct.DirectAdapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from langgraph_forge.deploy.base import AdapterConfig, DeploymentAdapter
from langgraph_forge.deploy.direct import DirectAdapter


class TestDirectAdapterProtocolConformance:
    def test_satisfies_deployment_adapter_protocol(self) -> None:
        assert isinstance(DirectAdapter(), DeploymentAdapter)

    def test_name_is_direct(self) -> None:
        assert DirectAdapter.name == "direct"

    def test_requires_no_extras(self) -> None:
        assert DirectAdapter.requires_extras == ()


class TestDirectAdapterPrepare:
    def test_prepare_returns_graph_unchanged(self) -> None:
        adapter = DirectAdapter()
        graph = MagicMock(name="compiled_graph")
        cfg = AdapterConfig(project_name="demo")

        assert adapter.prepare(graph, cfg) is graph


class TestDirectAdapterInvoke:
    @pytest.mark.asyncio
    async def test_invoke_awaits_graph_ainvoke_with_inputs(self) -> None:
        adapter = DirectAdapter()
        graph = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"messages": ["ok"]})

        result = await adapter.invoke(graph, {"messages": []})

        graph.ainvoke.assert_awaited_once_with({"messages": []})
        assert result == {"messages": ["ok"]}


class TestDirectAdapterTemplateFragment:
    def test_fragment_path_ends_in_direct(self) -> None:
        adapter = DirectAdapter()
        fragment = adapter.template_fragment()

        assert fragment.name == "direct"
