"""Azure AI Agent Service deployment adapter (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from langgraph_forge.deploy.base import AdapterConfig

_V02_MESSAGE = (
    "AzureAIAgentAdapter is a v0.1 contract stub; the concrete Azure "
    "integration lands in v0.2. Track the work or contribute at "
    "https://github.com/jieyao-MilestoneHub/langgraph-forge/issues."
)


class AzureAIAgentAdapter:
    """Deploy a compiled LangGraph to Azure AI Agent Service.

    Requires the ``azure`` optional extra::

        pip install langgraph-forge[azure]

    Adapter-specific options on :attr:`AdapterConfig.extra`:

    - ``endpoint``: Azure AI Foundry project endpoint URL.
    - ``agent_id``: reuse an existing agent id instead of registering
      a new one.
    - ``credential``: override the default ``DefaultAzureCredential``.
    """

    name: ClassVar[str] = "azure"
    requires_extras: ClassVar[tuple[str, ...]] = ("azure-ai-agents",)
    is_stub: ClassVar[bool] = True

    def prepare(self, graph: Any, config: AdapterConfig) -> Any:  # noqa: ARG002
        raise NotImplementedError(_V02_MESSAGE)

    async def invoke(self, deployable: Any, inputs: dict) -> dict:  # noqa: ARG002
        raise NotImplementedError(_V02_MESSAGE)

    def template_fragment(self) -> Path:
        return Path(__file__).parent.parent / "scaffold" / "templates" / "deploy_fragments" / "azure"
