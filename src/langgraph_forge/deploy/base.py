"""Deployment port: the Protocol every adapter satisfies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class AdapterConfig:
    """Per-invocation configuration handed to an adapter's ``prepare``.

    ``project_name`` names the deployable -- cloud targets register
    agents under this string, the CLI uses it as a directory name.

    ``extra`` is an opaque bag for adapter-specific options (Bedrock
    session identity, Vertex project + location, Azure endpoint URL,
    user-supplied IAM roles). Keeping these off the Protocol keeps
    adapters from leaking vendor concepts into the shared contract.
    """

    project_name: str
    extra: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class DeploymentAdapter(Protocol):
    """Port every deployment target implements.

    Adapters are discovered via the
    ``langgraph_forge.deployment_adapters`` entry-point group (see
    :mod:`langgraph_forge.deploy.registry`). Third-party packages can
    publish their own adapter simply by satisfying this Protocol and
    declaring the entry point -- the core library needs no diff.
    """

    name: str
    requires_extras: tuple[str, ...]

    def prepare(self, graph: Any, config: AdapterConfig) -> Any:
        """Turn a compiled LangGraph into a deployable handle.

        For local-only adapters this may be a pass-through returning
        the graph itself; cloud adapters typically register the agent
        with the target service and return the service-specific handle
        (e.g. a Bedrock ``agent_id`` or a Vertex ``reasoning_engine``
        resource).
        """
        ...

    async def invoke(self, deployable: Any, inputs: dict) -> dict:
        """Run one request against the prepared deployable."""
        ...

    def template_fragment(self) -> Path:
        """Return the path to this adapter's Jinja2 template fragment.

        The scaffold renderer walks this directory when generating a
        new project for the adapter, so every adapter owns its own
        deploy.py template. Third-party adapters can ship their
        fragment inside their own package.
        """
        ...
