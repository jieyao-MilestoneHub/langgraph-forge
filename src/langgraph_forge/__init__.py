"""langgraph-forge -- initialise LangGraph-based agent architectures.

Public API. Internal modules may change without notice between minor
versions; every symbol re-exported here is part of the stable surface.
"""

from langchain_core.tools import BaseTool
from langgraph.types import Command

from langgraph_forge._version import __version__
from langgraph_forge.builders.checkpoint import get_checkpointer
from langgraph_forge.builders.llm import get_model
from langgraph_forge.builders.mcp import load_mcp_tools
from langgraph_forge.builders.single import create_single_agent
from langgraph_forge.builders.supervisor import create_supervisor_agent
from langgraph_forge.core.errors import (
    ForgeConfigError,
    ForgeError,
    MissingExtraError,
)
from langgraph_forge.core.specs import (
    MCPConfig,
    MCPServerConfig,
    ModelSpec,
    SpecialistSpec,
)
from langgraph_forge.core.state import ForgeState
from langgraph_forge.deploy import DeploymentAdapter, DirectAdapter

__all__ = [
    "BaseTool",
    "Command",
    "DeploymentAdapter",
    "DirectAdapter",
    "ForgeConfigError",
    "ForgeError",
    "ForgeState",
    "MCPConfig",
    "MCPServerConfig",
    "MissingExtraError",
    "ModelSpec",
    "SpecialistSpec",
    "__version__",
    "create_single_agent",
    "create_supervisor_agent",
    "get_checkpointer",
    "get_model",
    "load_mcp_tools",
]
