"""Tests for langgraph_forge.core.specs.MCPServerConfig and MCPConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from langgraph_forge.core.specs import MCPConfig, MCPServerConfig


class TestStdioTransport:
    def test_valid_stdio_server(self) -> None:
        srv = MCPServerConfig(
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        )

        assert srv.command == "npx"

    def test_stdio_missing_command_rejected(self) -> None:
        with pytest.raises(ValidationError, match="command"):
            MCPServerConfig(transport="stdio")

    def test_stdio_with_url_rejected(self) -> None:
        with pytest.raises(ValidationError, match="url"):
            MCPServerConfig(transport="stdio", command="npx", url="https://example.com")


class TestNetworkTransport:
    @pytest.mark.parametrize("transport", ["sse", "streamable_http"])
    def test_valid_network_server(self, transport: str) -> None:
        srv = MCPServerConfig(transport=transport, url="https://example.com/mcp")  # type: ignore[arg-type]

        assert srv.url == "https://example.com/mcp"

    @pytest.mark.parametrize("transport", ["sse", "streamable_http"])
    def test_network_missing_url_rejected(self, transport: str) -> None:
        with pytest.raises(ValidationError, match="url"):
            MCPServerConfig(transport=transport)  # type: ignore[arg-type]

    @pytest.mark.parametrize("transport", ["sse", "streamable_http"])
    def test_network_with_command_rejected(self, transport: str) -> None:
        with pytest.raises(ValidationError, match="command"):
            MCPServerConfig(  # type: ignore[arg-type]
                transport=transport,
                url="https://example.com/mcp",
                command="npx",
            )


class TestInvalidTransport:
    def test_unknown_transport_rejected(self) -> None:
        with pytest.raises(ValidationError, match="transport"):
            MCPServerConfig(transport="telepathy", url="x")  # type: ignore[arg-type]


class TestMCPConfigAggregate:
    def test_empty_servers_accepted(self) -> None:
        cfg = MCPConfig(servers={})

        assert cfg.servers == {}

    def test_servers_mapping_preserved(self) -> None:
        srv = MCPServerConfig(transport="stdio", command="npx")
        cfg = MCPConfig(servers={"fs": srv})

        assert cfg.servers["fs"] is srv

    def test_frozen_rejects_mutation(self) -> None:
        cfg = MCPConfig(servers={})

        with pytest.raises(ValidationError, match="frozen|immutable"):
            cfg.servers = {"x": MCPServerConfig(transport="stdio", command="c")}  # type: ignore[misc]
