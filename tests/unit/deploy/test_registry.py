"""Tests for langgraph_forge.deploy.registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest

from langgraph_forge.deploy.registry import discover_adapters, get_adapter


class _ValidFake:
    name: ClassVar[str] = "fake"
    requires_extras: ClassVar[tuple[str, ...]] = ()

    def prepare(self, graph: Any, config: Any) -> Any:
        return graph

    async def invoke(self, deployable: Any, inputs: dict) -> dict:
        return inputs

    def template_fragment(self) -> Path:
        return Path("/tmp/fake")


class _InvalidFake:
    """Missing invoke and template_fragment -- should be filtered out."""

    name: ClassVar[str] = "broken"
    requires_extras: ClassVar[tuple[str, ...]] = ()


def _entry_point(name: str, cls: type[Any]) -> MagicMock:
    ep = MagicMock()
    ep.name = name
    ep.load = MagicMock(return_value=cls)
    return ep


class TestDiscoverAdapters:
    def test_empty_entry_points_returns_empty_dict(self) -> None:
        with patch(
            "langgraph_forge.deploy.registry.entry_points",
            return_value=(),
        ):
            result = discover_adapters()

        assert result == {}

    def test_valid_entry_point_included(self) -> None:
        with patch(
            "langgraph_forge.deploy.registry.entry_points",
            return_value=(_entry_point("fake", _ValidFake),),
        ):
            result = discover_adapters()

        assert result == {"fake": _ValidFake}

    def test_invalid_entry_point_excluded(self) -> None:
        with patch(
            "langgraph_forge.deploy.registry.entry_points",
            return_value=(_entry_point("broken", _InvalidFake),),
        ):
            result = discover_adapters()

        assert result == {}

    def test_multiple_entry_points_merged(self) -> None:
        class _AnotherValid:
            name: ClassVar[str] = "other"
            requires_extras: ClassVar[tuple[str, ...]] = ()

            def prepare(self, graph: Any, config: Any) -> Any:
                return graph

            async def invoke(self, deployable: Any, inputs: dict) -> dict:
                return inputs

            def template_fragment(self) -> Path:
                return Path("/tmp/other")

        with patch(
            "langgraph_forge.deploy.registry.entry_points",
            return_value=(
                _entry_point("fake", _ValidFake),
                _entry_point("other", _AnotherValid),
            ),
        ):
            result = discover_adapters()

        assert set(result.keys()) == {"fake", "other"}


class TestGetAdapter:
    def test_returns_class_when_registered(self) -> None:
        with patch(
            "langgraph_forge.deploy.registry.entry_points",
            return_value=(_entry_point("fake", _ValidFake),),
        ):
            cls = get_adapter("fake")

        assert cls is _ValidFake

    def test_raises_keyerror_when_missing(self) -> None:
        with (
            patch(
                "langgraph_forge.deploy.registry.entry_points",
                return_value=(),
            ),
            pytest.raises(KeyError, match="unknown"),
        ):
            get_adapter("unknown")
