"""Tests for langgraph_forge.core.specs.ThreadConfig."""

from __future__ import annotations

import dataclasses

import pytest

from langgraph_forge.core.specs import ThreadConfig


class TestThreadConfigConstruction:
    def test_thread_id_required(self) -> None:
        cfg = ThreadConfig(thread_id="run-42")

        assert cfg.thread_id == "run-42"

    def test_default_checkpoint_ns_is_empty_string(self) -> None:
        # LangGraph treats missing namespace as empty string; our default
        # mirrors that to avoid surprising behaviour when callers omit it.
        cfg = ThreadConfig(thread_id="run-42")

        assert cfg.checkpoint_ns == ""

    def test_default_checkpoint_id_is_none(self) -> None:
        cfg = ThreadConfig(thread_id="run-42")

        assert cfg.checkpoint_id is None

    def test_explicit_namespace_preserved(self) -> None:
        cfg = ThreadConfig(thread_id="run-42", checkpoint_ns="tenant-a")

        assert cfg.checkpoint_ns == "tenant-a"

    def test_explicit_checkpoint_id_preserved(self) -> None:
        cfg = ThreadConfig(thread_id="run-42", checkpoint_id="ckpt-7")

        assert cfg.checkpoint_id == "ckpt-7"


class TestThreadConfigImmutability:
    def test_frozen_rejects_field_assignment(self) -> None:
        cfg = ThreadConfig(thread_id="run-42")

        with pytest.raises(dataclasses.FrozenInstanceError):
            cfg.thread_id = "renamed"  # type: ignore[misc]


class TestThreadConfigToLangGraph:
    def test_minimal_shape(self) -> None:
        # Even with empty namespace and no checkpoint id, the configurable
        # dict shape LangGraph expects has thread_id and checkpoint_ns.
        cfg = ThreadConfig(thread_id="run-42")

        assert cfg.to_langgraph() == {
            "configurable": {"thread_id": "run-42", "checkpoint_ns": ""}
        }

    def test_includes_checkpoint_id_when_set(self) -> None:
        cfg = ThreadConfig(thread_id="run-42", checkpoint_id="ckpt-7")

        assert cfg.to_langgraph() == {
            "configurable": {
                "thread_id": "run-42",
                "checkpoint_ns": "",
                "checkpoint_id": "ckpt-7",
            }
        }

    def test_includes_namespace(self) -> None:
        cfg = ThreadConfig(thread_id="run-42", checkpoint_ns="tenant-a")

        assert cfg.to_langgraph() == {
            "configurable": {"thread_id": "run-42", "checkpoint_ns": "tenant-a"}
        }

    def test_omits_checkpoint_id_when_none(self) -> None:
        cfg = ThreadConfig(thread_id="run-42")

        assert "checkpoint_id" not in cfg.to_langgraph()["configurable"]
