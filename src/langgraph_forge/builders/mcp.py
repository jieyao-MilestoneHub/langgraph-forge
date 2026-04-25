"""MCP tool loader, backed by ``langchain-mcp-adapters``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_mcp_adapters.client import MultiServerMCPClient

from langgraph_forge.core.specs import MCPConfig

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


async def load_mcp_tools(config: MCPConfig) -> list[BaseTool]:
    """Instantiate the upstream client and collect tools from every server.

    The :class:`MCPConfig` is translated to the per-server dict shape
    expected by :class:`MultiServerMCPClient` by calling
    ``model_dump(exclude_none=True)`` on each :class:`MCPServerConfig`.
    ``None`` fields (url for stdio, command for network transports)
    are dropped so the upstream client does not see ambiguous input.

    The returned tools are ready to pass to either
    :func:`create_single_agent` or :class:`SpecialistSpec.tools`.
    """
    servers_dict = {name: srv.model_dump(exclude_none=True) for name, srv in config.servers.items()}
    # Upstream types `connections` as `dict[str, Connection]` (a TypedDict
    # union). Our model_dump output satisfies it structurally at runtime
    # but pyright sees only `dict[str, dict[str, Any]]` and refuses the
    # narrowing. Ignore locally; runtime path is exercised by the unit
    # tests that mock get_tools.
    client = MultiServerMCPClient(servers_dict)  # pyright: ignore[reportArgumentType]
    return await client.get_tools()
