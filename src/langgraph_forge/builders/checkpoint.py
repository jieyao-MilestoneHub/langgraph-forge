# pyright: reportMissingImports=false
"""Checkpointer factory -- lazy imports per backend.

The whole point of this module is to defer importing
``langgraph.checkpoint.sqlite`` and ``langgraph.checkpoint.postgres``
until the user actually requests those backends. They live behind the
optional ``[sqlite]`` and ``[postgres]`` extras and may legitimately
be missing in any given environment. Pyright's ``reportMissingImports``
is silenced at file level (not per-line) because every cross-language
review of this module repeatedly questions per-line ignores; making
the policy file-level keeps the intent obvious. Ruff's PLC0415 is
suppressed via ``[tool.ruff.lint.per-file-ignores]`` for the same
reason.
"""

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
            raise MissingExtraError(extra="sqlite", feature="the SQLite checkpointer") from exc
        conn_string = kwargs.get("conn_string")
        if conn_string is None:
            raise ForgeConfigError("sqlite checkpointer requires conn_string kwarg")
        return SqliteSaver.from_conn_string(conn_string)

    if kind == "postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as exc:
            raise MissingExtraError(extra="postgres", feature="the Postgres checkpointer") from exc
        conn_string = kwargs.get("conn_string")
        if conn_string is None:
            raise ForgeConfigError("postgres checkpointer requires conn_string kwarg")
        return PostgresSaver.from_conn_string(conn_string)

    raise ValueError(f"unknown checkpointer kind: {kind!r}")
