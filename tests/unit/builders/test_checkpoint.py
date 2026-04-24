"""Tests for langgraph_forge.builders.checkpoint.get_checkpointer."""

from __future__ import annotations

from unittest.mock import patch, sentinel

import pytest
from langgraph.checkpoint.memory import MemorySaver

from langgraph_forge.builders.checkpoint import get_checkpointer
from langgraph_forge.core.errors import ForgeConfigError


class TestMemoryBackend:
    def test_memory_returns_memory_saver(self) -> None:
        saver = get_checkpointer("memory")

        assert isinstance(saver, MemorySaver)


class TestSqliteBackend:
    def test_missing_conn_string_raises_config_error(self) -> None:
        with pytest.raises(ForgeConfigError, match="conn_string"):
            get_checkpointer("sqlite")

    def test_conn_string_forwarded_to_sqlite_saver(self) -> None:
        with patch("langgraph.checkpoint.sqlite.SqliteSaver") as mock_cls:
            mock_cls.from_conn_string.return_value = sentinel.saver
            result = get_checkpointer("sqlite", conn_string="test.db")

        mock_cls.from_conn_string.assert_called_once_with("test.db")
        assert result is sentinel.saver


class TestPostgresBackend:
    def test_missing_conn_string_raises_config_error(self) -> None:
        with pytest.raises(ForgeConfigError, match="conn_string"):
            get_checkpointer("postgres")

    def test_conn_string_forwarded_to_postgres_saver(self) -> None:
        with patch("langgraph.checkpoint.postgres.PostgresSaver") as mock_cls:
            mock_cls.from_conn_string.return_value = sentinel.saver
            result = get_checkpointer("postgres", conn_string="postgresql://x")

        mock_cls.from_conn_string.assert_called_once_with("postgresql://x")
        assert result is sentinel.saver


class TestUnknownBackend:
    def test_unknown_kind_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="unknown checkpointer kind"):
            get_checkpointer("telepathy")  # type: ignore[arg-type]
