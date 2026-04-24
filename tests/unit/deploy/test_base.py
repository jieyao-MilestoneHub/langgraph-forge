"""Tests for langgraph_forge.deploy.base (Protocol + AdapterConfig)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import pytest

from langgraph_forge.deploy.base import AdapterConfig, DeploymentAdapter


class _GoodAdapter:
    """Minimum concrete implementation used to probe the Protocol contract."""

    name: ClassVar[str] = "good"
    requires_extras: ClassVar[tuple[str, ...]] = ()

    def prepare(self, graph: Any, config: AdapterConfig) -> Any:
        return graph

    async def invoke(self, deployable: Any, inputs: dict) -> dict:
        return inputs

    def template_fragment(self) -> Path:
        return Path("/tmp/x")


class _MissingInvokeAdapter:
    name: ClassVar[str] = "bad"
    requires_extras: ClassVar[tuple[str, ...]] = ()

    def prepare(self, graph: Any, config: AdapterConfig) -> Any:
        return graph

    def template_fragment(self) -> Path:
        return Path("/tmp/x")


class TestDeploymentAdapterProtocol:
    def test_runtime_checkable_accepts_valid_implementation(self) -> None:
        assert isinstance(_GoodAdapter(), DeploymentAdapter)

    def test_runtime_checkable_rejects_missing_method(self) -> None:
        # _MissingInvokeAdapter is missing invoke; runtime_checkable catches it.
        assert not isinstance(_MissingInvokeAdapter(), DeploymentAdapter)


class TestAdapterConfig:
    def test_project_name_required(self) -> None:
        cfg = AdapterConfig(project_name="demo")

        assert cfg.project_name == "demo"

    def test_extra_defaults_to_empty_dict(self) -> None:
        cfg = AdapterConfig(project_name="demo")

        assert cfg.extra == {}

    def test_extra_accepts_arbitrary_payload(self) -> None:
        cfg = AdapterConfig(project_name="demo", extra={"region": "us-west-2"})

        assert cfg.extra == {"region": "us-west-2"}

    def test_frozen_rejects_mutation(self) -> None:
        cfg = AdapterConfig(project_name="demo")

        with pytest.raises((AttributeError, Exception)):
            cfg.project_name = "renamed"  # type: ignore[misc]
