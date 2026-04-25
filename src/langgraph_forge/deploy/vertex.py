"""GCP Vertex Agent Engine deployment adapter (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from langgraph_forge.deploy.base import AdapterConfig

_V02_MESSAGE = (
    "VertexAgentEngineAdapter is a v0.1 contract stub; the concrete GCP "
    "integration lands in v0.2. Track the work or contribute at "
    "https://github.com/jieyao-MilestoneHub/langgraph-forge/issues."
)


class VertexAgentEngineAdapter:
    """Deploy a compiled LangGraph to Google Vertex AI Agent Engine.

    Requires the ``vertex`` optional extra::

        pip install langgraph-forge[vertex]

    Adapter-specific options on :attr:`AdapterConfig.extra`:

    - ``project``: GCP project id.
    - ``location``: region (e.g. ``us-central1``).
    - ``reasoning_engine_id``: reuse an existing engine instead of
      registering a new one.
    """

    name: ClassVar[str] = "vertex"
    requires_extras: ClassVar[tuple[str, ...]] = ("google-cloud-aiplatform",)
    is_stub: ClassVar[bool] = True

    def prepare(self, graph: Any, config: AdapterConfig) -> Any:
        raise NotImplementedError(_V02_MESSAGE)

    async def invoke(self, deployable: Any, inputs: dict) -> dict:
        raise NotImplementedError(_V02_MESSAGE)

    def template_fragment(self) -> Path:
        return (
            Path(__file__).parent.parent / "scaffold" / "templates" / "deploy_fragments" / "vertex"
        )
