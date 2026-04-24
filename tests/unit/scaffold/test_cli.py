"""Tests for langgraph_forge.scaffold.cli."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from langgraph_forge._version import __version__
from langgraph_forge.scaffold.cli import app

runner = CliRunner()


class TestVersionCommand:
    def test_prints_installed_version(self) -> None:
        result = runner.invoke(app, ["version"])

        assert __version__ in result.stdout


class TestListProviders:
    def test_lists_at_least_anthropic_and_openai(self) -> None:
        result = runner.invoke(app, ["list-providers"])

        assert {"anthropic", "openai"}.issubset(set(result.stdout.split()))


class TestListPatterns:
    def test_lists_single_and_supervisor(self) -> None:
        result = runner.invoke(app, ["list-patterns"])

        assert {"single", "supervisor"}.issubset(set(result.stdout.split()))


class TestListDeploy:
    def test_shows_adapters_from_registry(self) -> None:
        from typing import Any, ClassVar

        class _FakeAdapter:
            name: ClassVar[str] = "fake"
            requires_extras: ClassVar[tuple[str, ...]] = ("foo",)

            def prepare(self, graph: Any, config: Any) -> Any:
                return graph

            async def invoke(self, deployable: Any, inputs: dict) -> dict:
                return inputs

            def template_fragment(self) -> Path:
                return Path("/tmp/fake")

        with patch(
            "langgraph_forge.scaffold.cli.discover_adapters",
            return_value={"fake": _FakeAdapter},
        ):
            result = runner.invoke(app, ["list-deploy"])

        assert "fake" in result.stdout


class TestDoctorCommand:
    def test_unknown_adapter_exits_nonzero(self) -> None:
        with patch(
            "langgraph_forge.scaffold.cli.discover_adapters",
            return_value={},
        ):
            result = runner.invoke(app, ["doctor", "--deploy", "nonexistent"])

        assert result.exit_code != 0


class TestInitCommand:
    def test_init_creates_target_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "demo_project"

        with patch("langgraph_forge.scaffold.cli.render_project") as mock_render:
            mock_render.return_value = []
            result = runner.invoke(
                app,
                [
                    "init",
                    str(target),
                    "--provider",
                    "anthropic",
                    "--pattern",
                    "supervisor",
                    "--deploy",
                    "direct",
                    "--no-input",
                ],
            )

        assert result.exit_code == 0

    def test_init_passes_context_to_renderer(self, tmp_path: Path) -> None:
        target = tmp_path / "demo_project"

        with patch("langgraph_forge.scaffold.cli.render_project") as mock_render:
            mock_render.return_value = []
            runner.invoke(
                app,
                [
                    "init",
                    str(target),
                    "--provider",
                    "anthropic",
                    "--pattern",
                    "supervisor",
                    "--deploy",
                    "direct",
                    "--no-input",
                ],
            )

        _, kwargs = mock_render.call_args
        assert kwargs["context"]["provider"] == "anthropic"
