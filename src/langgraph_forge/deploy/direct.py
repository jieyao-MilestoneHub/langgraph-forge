"""Local-execution deployment adapter.

The reference implementation of :class:`DeploymentAdapter`: no SDK,
no registration, no network call. Users pick this adapter when they
host the LangGraph graph themselves (FastAPI app, Lambda function,
Modal container, langgraph-cli dev server, etc.).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from langgraph_forge.deploy.base import AdapterConfig


class DirectAdapter:
    """Run a compiled LangGraph locally.

    ``prepare`` is the identity: there is nothing to register.
    ``invoke`` delegates to the graph's own ``ainvoke`` method.
    """

    name: ClassVar[str] = "direct"
    requires_extras: ClassVar[tuple[str, ...]] = ()

    def prepare(self, graph: Any, config: AdapterConfig) -> Any:  # noqa: ARG002
        return graph

    async def invoke(self, deployable: Any, inputs: dict) -> dict:
        return await deployable.ainvoke(inputs)

    def template_fragment(self) -> Path:
        return Path(__file__).parent.parent / "scaffold" / "templates" / "deploy_fragments" / "direct"
