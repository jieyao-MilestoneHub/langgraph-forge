"""Tests for langgraph_forge.core.errors."""

from __future__ import annotations

from langgraph_forge.core.errors import (
    ForgeConfigError,
    ForgeError,
    MissingExtraError,
)


class TestForgeErrorHierarchy:
    def test_forge_config_error_is_forge_error(self) -> None:
        err = ForgeConfigError("bad config")
        assert isinstance(err, ForgeError)

    def test_missing_extra_error_is_forge_error(self) -> None:
        err = MissingExtraError(extra="bedrock", feature="Bedrock AgentCore")
        assert isinstance(err, ForgeError)


class TestMissingExtraErrorMessage:
    def test_message_contains_extra_name(self) -> None:
        err = MissingExtraError(extra="bedrock", feature="Bedrock AgentCore")
        assert "bedrock" in str(err)

    def test_message_contains_feature_name(self) -> None:
        err = MissingExtraError(extra="vertex", feature="Vertex AI Agent Engine")
        assert "Vertex AI Agent Engine" in str(err)

    def test_message_contains_pip_install_hint(self) -> None:
        err = MissingExtraError(extra="azure", feature="Azure AI Agent")
        assert "pip install langgraph-forge[azure]" in str(err)

    def test_extra_attribute_preserved(self) -> None:
        err = MissingExtraError(extra="bedrock", feature="Bedrock AgentCore")
        assert err.extra == "bedrock"

    def test_feature_attribute_preserved(self) -> None:
        err = MissingExtraError(extra="bedrock", feature="Bedrock AgentCore")
        assert err.feature == "Bedrock AgentCore"
