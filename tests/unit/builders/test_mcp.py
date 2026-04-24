"""Tests for langgraph_forge.builders.mcp.load_mcp_tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from langgraph_forge.builders.mcp import load_mcp_tools
from langgraph_forge.core.specs import MCPConfig, MCPServerConfig


def _client_mock(get_tools_returns: list) -> MagicMock:
    instance = MagicMock()
    instance.get_tools = AsyncMock(return_value=get_tools_returns)
    return instance


class TestLoadMCPToolsClientConstruction:
    @pytest.mark.asyncio
    async def test_stdio_server_dict_shape(self) -> None:
        cfg = MCPConfig(
            servers={
                "fs": MCPServerConfig(
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                ),
            }
        )
        with patch(
            "langgraph_forge.builders.mcp.MultiServerMCPClient",
            return_value=_client_mock([]),
        ) as mock_cls:
            await load_mcp_tools(cfg)

        assert mock_cls.call_args[0][0] == {
            "fs": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                "env": {},
            }
        }

    @pytest.mark.asyncio
    async def test_network_server_dict_shape(self) -> None:
        cfg = MCPConfig(
            servers={
                "weather": MCPServerConfig(
                    transport="streamable_http",
                    url="https://weather.example.com/mcp",
                    env={"AUTH": "bearer"},
                ),
            }
        )
        with patch(
            "langgraph_forge.builders.mcp.MultiServerMCPClient",
            return_value=_client_mock([]),
        ) as mock_cls:
            await load_mcp_tools(cfg)

        assert mock_cls.call_args[0][0] == {
            "weather": {
                "transport": "streamable_http",
                "args": [],
                "url": "https://weather.example.com/mcp",
                "env": {"AUTH": "bearer"},
            }
        }


class TestLoadMCPToolsReturnValue:
    @pytest.mark.asyncio
    async def test_returns_get_tools_result(self) -> None:
        cfg = MCPConfig(servers={})
        fake_tools = [MagicMock(name="tool_a"), MagicMock(name="tool_b")]
        with patch(
            "langgraph_forge.builders.mcp.MultiServerMCPClient",
            return_value=_client_mock(fake_tools),
        ):
            result = await load_mcp_tools(cfg)

        assert result == fake_tools

    @pytest.mark.asyncio
    async def test_empty_config_returns_empty_list(self) -> None:
        cfg = MCPConfig(servers={})
        with patch(
            "langgraph_forge.builders.mcp.MultiServerMCPClient",
            return_value=_client_mock([]),
        ):
            result = await load_mcp_tools(cfg)

        assert result == []
