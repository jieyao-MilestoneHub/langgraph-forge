"""Checkpointer factory — lazy imports per backend."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from langgraph_forge.core.errors import ForgeConfigError, MissingExtraError

CheckpointerKind = Literal["memory", "sqlite", "postgres"]


def get_checkpointer(kind: CheckpointerKind, **kwargs: Any) -> BaseCheckpointSaver:
    """Instantiate a LangGraph checkpointer for the given backend.

    ``memory`` is always available (ships with ``langgraph``).
    ``sqlite`` requires the optional ``langgraph-forge[sqlite]`` extra;
    ``postgres`` requires ``langgraph-forge[postgres]``. Both raise
    :class:`MissingExtraError` with the exact pip hint when their
    package is not installed.

    Additional kwargs are backend-specific:
    - sqlite / postgres: ``conn_string`` (required).
    """
    if kind == "memory":
        return MemorySaver()

    if kind == "sqlite":
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError as exc:
            raise MissingExtraError(
                extra="sqlite", feature="the SQLite checkpointer"
            ) from exc
        conn_string = kwargs.get("conn_string")
        if conn_string is None:
            raise ForgeConfigError(
                "sqlite checkpointer requires conn_string kwarg"
            )
        return SqliteSaver.from_conn_string(conn_string)

    if kind == "postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as exc:
            raise MissingExtraError(
                extra="postgres", feature="the Postgres checkpointer"
            ) from exc
        conn_string = kwargs.get("conn_string")
        if conn_string is None:
            raise ForgeConfigError(
                "postgres checkpointer requires conn_string kwarg"
            )
        return PostgresSaver.from_conn_string(conn_string)

    raise ValueError(f"unknown checkpointer kind: {kind!r}")
