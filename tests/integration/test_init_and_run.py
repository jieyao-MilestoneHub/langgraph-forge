"""Integration: ``langgraph-forge init`` scaffolds a valid project tree."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from langgraph_forge.scaffold.cli import app

runner = CliRunner()


@pytest.fixture
def scaffolded(tmp_path: Path) -> Path:
    target = tmp_path / "demo_agent"
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
    assert result.exit_code == 0, result.output
    return target


class TestScaffoldedTreeLayout:
    def test_expected_files_exist(self, scaffolded: Path) -> None:
        existing = sorted(
            p.relative_to(scaffolded).as_posix() for p in scaffolded.rglob("*") if p.is_file()
        )

        expected = sorted(
            [
                ".env.example",
                ".gitignore",
                "README.md",
                "pyproject.toml",
                "src/demo_agent/__init__.py",
                "src/demo_agent/deploy.py",
                "src/demo_agent/graph.py",
                "src/demo_agent/main.py",
                "src/demo_agent/providers.py",
                "src/demo_agent/specialists.py",
                "tests/unit/test_graph.py",
            ]
        )

        assert existing == expected


class TestJinjaSubstitution:
    def test_package_name_substituted_in_main(self, scaffolded: Path) -> None:
        content = (scaffolded / "src" / "demo_agent" / "main.py").read_text(encoding="utf-8")

        assert "demo_agent" in content

    def test_provider_substituted_in_readme(self, scaffolded: Path) -> None:
        content = (scaffolded / "README.md").read_text(encoding="utf-8")

        assert "anthropic" in content

    def test_project_name_substituted_in_pyproject(self, scaffolded: Path) -> None:
        content = (scaffolded / "pyproject.toml").read_text(encoding="utf-8")

        assert 'name = "demo_agent"' in content


class TestMultipleCombinations:
    @pytest.mark.parametrize(
        ("pattern", "provider", "deploy"),
        [
            ("supervisor", "anthropic", "direct"),
            ("single", "openai", "direct"),
            ("supervisor", "bedrock", "bedrock"),
            ("supervisor", "google", "vertex"),
            ("single", "grok", "direct"),
            ("swarm", "anthropic", "direct"),
            ("hierarchical", "anthropic", "direct"),
            ("router", "anthropic", "direct"),
            ("custom", "anthropic", "direct"),
        ],
    )
    def test_combination_scaffolds_successfully(
        self,
        tmp_path: Path,
        pattern: str,
        provider: str,
        deploy: str,
    ) -> None:
        target = tmp_path / f"demo_{pattern}_{provider}_{deploy}"

        result = runner.invoke(
            app,
            [
                "init",
                str(target),
                "--provider",
                provider,
                "--pattern",
                pattern,
                "--deploy",
                deploy,
                "--no-input",
            ],
        )

        assert result.exit_code == 0, result.output


class TestOverwriteBehaviour:
    def test_existing_target_without_force_fails(self, scaffolded: Path) -> None:
        result = runner.invoke(
            app,
            [
                "init",
                str(scaffolded),
                "--provider",
                "anthropic",
                "--pattern",
                "supervisor",
                "--deploy",
                "direct",
                "--no-input",
            ],
        )

        assert result.exit_code != 0

    def test_existing_target_with_force_succeeds(self, scaffolded: Path) -> None:
        result = runner.invoke(
            app,
            [
                "init",
                str(scaffolded),
                "--provider",
                "anthropic",
                "--pattern",
                "supervisor",
                "--deploy",
                "direct",
                "--no-input",
                "--force",
            ],
        )

        assert result.exit_code == 0, result.output
