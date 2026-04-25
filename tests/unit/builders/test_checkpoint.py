"""Tests for langgraph_forge.builders.checkpoint.get_checkpointer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, sentinel

import pytest
from langgraph.checkpoint.memory import MemorySaver

from langgraph_forge.builders.checkpoint import get_checkpointer
from langgraph_forge.core.errors import ForgeConfigError


def _injected_module(saver_attr_name: str, saver_class: object) -> dict:
    """Build a sys.modules patch that fakes the optional checkpoint package.

    The implementation does ``from langgraph.checkpoint.sqlite import
    SqliteSaver`` (or postgres). Without the optional extra installed,
    that import raises ImportError before we reach the ForgeConfigError
    branch. We inject a fake module so the import succeeds and the
    behaviour we care about (conn_string handling, dispatch) runs.
    """
    fake_module = MagicMock()
    setattr(fake_module, saver_attr_name, saver_class)
    return fake_module


class TestMemoryBackend:
    def test_memory_returns_memory_saver(self) -> None:
        saver = get_checkpointer("memory")

        assert isinstance(saver, MemorySaver)


class TestSqliteBackend:
    def test_missing_conn_string_raises_config_error(self) -> None:
        # Inject a fake sqlite module so the optional-import path
        # succeeds; the test exercises the conn_string-missing branch.
        fake_module = _injected_module("SqliteSaver", MagicMock())
        with (
            patch.dict("sys.modules", {"langgraph.checkpoint.sqlite": fake_module}),
            pytest.raises(ForgeConfigError, match="conn_string"),
        ):
            get_checkpointer("sqlite")

    def test_conn_string_forwarded_to_sqlite_saver(self) -> None:
        fake_saver_class = MagicMock()
        fake_saver_class.from_conn_string.return_value = sentinel.saver
        fake_module = _injected_module("SqliteSaver", fake_saver_class)
        with patch.dict("sys.modules", {"langgraph.checkpoint.sqlite": fake_module}):
            result = get_checkpointer("sqlite", conn_string="test.db")

        fake_saver_class.from_conn_string.assert_called_once_with("test.db")
        assert result is sentinel.saver


class TestPostgresBackend:
    def test_missing_conn_string_raises_config_error(self) -> None:
        fake_module = _injected_module("PostgresSaver", MagicMock())
        with (
            patch.dict("sys.modules", {"langgraph.checkpoint.postgres": fake_module}),
            pytest.raises(ForgeConfigError, match="conn_string"),
        ):
            get_checkpointer("postgres")

    def test_conn_string_forwarded_to_postgres_saver(self) -> None:
        fake_saver_class = MagicMock()
        fake_saver_class.from_conn_string.return_value = sentinel.saver
        fake_module = _injected_module("PostgresSaver", fake_saver_class)
        with patch.dict("sys.modules", {"langgraph.checkpoint.postgres": fake_module}):
            result = get_checkpointer("postgres", conn_string="postgresql://x")

        fake_saver_class.from_conn_string.assert_called_once_with("postgresql://x")
        assert result is sentinel.saver


class TestUnknownBackend:
    def test_unknown_kind_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="unknown checkpointer kind"):
            get_checkpointer("telepathy")  # type: ignore[arg-type]
