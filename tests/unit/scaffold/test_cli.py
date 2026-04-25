"""Tests for langgraph_forge.scaffold.cli."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar
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


def _fake_adapter_class(*, is_stub_value: bool | None = None) -> type:
    """Build a Protocol-conforming fake adapter for CLI tests.

    Pass is_stub_value=True / False to set the attribute explicitly;
    pass None (default) to leave it absent so getattr defaults take over.
    """

    class _FakeAdapter:
        name: ClassVar[str] = "fake"
        requires_extras: ClassVar[tuple[str, ...]] = ("foo",)

        def prepare(self, graph: Any, config: Any) -> Any:
            return graph

        async def invoke(self, deployable: Any, inputs: dict) -> dict:
            return inputs

        def template_fragment(self) -> Path:
            return Path("/tmp/fake")

    if is_stub_value is not None:
        _FakeAdapter.is_stub = is_stub_value  # type: ignore[attr-defined]
    return _FakeAdapter


class TestListDeploy:
    def test_shows_adapters_from_registry(self) -> None:
        with patch(
            "langgraph_forge.scaffold.cli.discover_adapters",
            return_value={"fake": _fake_adapter_class()},
        ):
            result = runner.invoke(app, ["list-deploy"])

        assert "fake" in result.stdout

    def test_marks_stub_adapters_in_output(self) -> None:
        with patch(
            "langgraph_forge.scaffold.cli.discover_adapters",
            return_value={"fake": _fake_adapter_class(is_stub_value=True)},
        ):
            result = runner.invoke(app, ["list-deploy"])

        # Output contains a stub marker referencing v0.2 so the user
        # sees "scaffold-only, runtime planned" without reading docs.
        assert "v0.2" in result.stdout

    def test_does_not_mark_non_stub_adapters(self) -> None:
        with patch(
            "langgraph_forge.scaffold.cli.discover_adapters",
            return_value={"fake": _fake_adapter_class(is_stub_value=False)},
        ):
            result = runner.invoke(app, ["list-deploy"])

        assert "v0.2" not in result.stdout

    def test_treats_missing_attr_as_non_stub(self) -> None:
        with patch(
            "langgraph_forge.scaffold.cli.discover_adapters",
            return_value={"fake": _fake_adapter_class()},
        ):
            result = runner.invoke(app, ["list-deploy"])

        assert "v0.2" not in result.stdout


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

    def test_init_warns_when_using_stub_adapter(self, tmp_path: Path) -> None:
        # Real bedrock adapter is_stub=True; init should print a warning
        # so the user does not believe their scaffolded project will deploy.
        target = tmp_path / "demo_stub_warn"

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
                    "bedrock",
                    "--no-input",
                ],
            )

        assert "v0.2" in result.output

    def test_init_does_not_warn_for_direct_adapter(self, tmp_path: Path) -> None:
        target = tmp_path / "demo_no_warn"

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

        assert "v0.2" not in result.output
