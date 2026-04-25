"""Tests for cloud deployment adapter stubs (bedrock, vertex, azure)."""

from __future__ import annotations

from typing import Any

import pytest

from langgraph_forge.deploy.azure import AzureAIAgentAdapter
from langgraph_forge.deploy.base import AdapterConfig, DeploymentAdapter
from langgraph_forge.deploy.bedrock import BedrockAgentCoreAdapter
from langgraph_forge.deploy.direct import DirectAdapter
from langgraph_forge.deploy.vertex import VertexAgentEngineAdapter

CLOUD_ADAPTERS: list[tuple[str, type[Any], str, str]] = [
    ("bedrock", BedrockAgentCoreAdapter, "bedrock", "bedrock"),
    ("vertex", VertexAgentEngineAdapter, "vertex", "vertex"),
    ("azure", AzureAIAgentAdapter, "azure", "azure"),
]


class TestCloudStubProtocolConformance:
    @pytest.mark.parametrize(
        ("cls_name", "cls", "expected_name", "_"),
        CLOUD_ADAPTERS,
    )
    def test_satisfies_protocol(
        self,
        cls_name: str,
        cls: type[Any],
        expected_name: str,
        _: str,
    ) -> None:
        assert isinstance(cls(), DeploymentAdapter)

    @pytest.mark.parametrize(
        ("cls_name", "cls", "expected_name", "_"),
        CLOUD_ADAPTERS,
    )
    def test_name_matches_expected(
        self,
        cls_name: str,
        cls: type[Any],
        expected_name: str,
        _: str,
    ) -> None:
        assert cls.name == expected_name

    @pytest.mark.parametrize(
        ("cls_name", "cls", "expected_name", "_"),
        CLOUD_ADAPTERS,
    )
    def test_requires_extras_not_empty(
        self,
        cls_name: str,
        cls: type[Any],
        expected_name: str,
        _: str,
    ) -> None:
        # Every cloud adapter pulls in at least one third-party SDK, so
        # the extras tuple is never empty.
        assert len(cls.requires_extras) >= 1


class TestCloudStubsRaiseNotImplementedUntilV02:
    @pytest.mark.parametrize(("_", "cls", "__", "___"), CLOUD_ADAPTERS)
    def test_prepare_raises_not_implemented(
        self,
        _: str,
        cls: type[Any],
        __: str,
        ___: str,
    ) -> None:
        with pytest.raises(NotImplementedError, match=r"v0\.2"):
            cls().prepare(graph=None, config=AdapterConfig(project_name="demo"))

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("_", "cls", "__", "___"), CLOUD_ADAPTERS)
    async def test_invoke_raises_not_implemented(
        self,
        _: str,
        cls: type[Any],
        __: str,
        ___: str,
    ) -> None:
        with pytest.raises(NotImplementedError, match=r"v0\.2"):
            await cls().invoke(deployable=None, inputs={})


class TestCloudStubTemplateFragmentPath:
    @pytest.mark.parametrize(
        ("_", "cls", "__", "fragment_name"),
        CLOUD_ADAPTERS,
    )
    def test_fragment_path_matches_adapter_name(
        self,
        _: str,
        cls: type[Any],
        __: str,
        fragment_name: str,
    ) -> None:
        fragment = cls().template_fragment()

        assert fragment.name == fragment_name


class TestCloudStubsDeclareStubFlag:
    """Stub status is structural, not a hardcoded list in the CLI.

    Each cloud adapter declares ``is_stub: ClassVar[bool] = True`` so the
    CLI (and any third-party introspection) can detect "scaffolding works
    but runtime calls raise NotImplementedError" without reading docs.
    """

    @pytest.mark.parametrize(("_", "cls", "__", "___"), CLOUD_ADAPTERS)
    def test_class_attr_is_true(
        self,
        _: str,
        cls: type[Any],
        __: str,
        ___: str,
    ) -> None:
        assert cls.is_stub is True

    def test_direct_adapter_not_marked_as_stub(self) -> None:
        # DirectAdapter does not declare is_stub; getattr returns False.
        assert getattr(DirectAdapter, "is_stub", False) is False
