"""AWS Bedrock AgentCore Runtime deployment adapter (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from langgraph_forge.deploy.base import AdapterConfig

_V02_MESSAGE = (
    "BedrockAgentCoreAdapter is a v0.1 contract stub; the concrete AWS "
    "integration lands in v0.2. Track the work or contribute at "
    "https://github.com/jieyao-MilestoneHub/langgraph-forge/issues."
)


class BedrockAgentCoreAdapter:
    """Deploy a compiled LangGraph to AWS Bedrock AgentCore Runtime.

    Requires the ``bedrock`` optional extra::

        pip install langgraph-forge[bedrock]

    Adapter-specific options on :attr:`AdapterConfig.extra`:

    - ``region``: AWS region (default resolved from env).
    - ``agent_id``: reuse an existing agent id instead of registering
      a new one.
    - ``session_identity``: Cognito / Okta / Entra ID identity pool
      pass-through.
    """

    name: ClassVar[str] = "bedrock"
    requires_extras: ClassVar[tuple[str, ...]] = ("boto3", "bedrock-agentcore")

    def prepare(self, graph: Any, config: AdapterConfig) -> Any:  # noqa: ARG002
        raise NotImplementedError(_V02_MESSAGE)

    async def invoke(self, deployable: Any, inputs: dict) -> dict:  # noqa: ARG002
        raise NotImplementedError(_V02_MESSAGE)

    def template_fragment(self) -> Path:
        return Path(__file__).parent.parent / "scaffold" / "templates" / "deploy_fragments" / "bedrock"
