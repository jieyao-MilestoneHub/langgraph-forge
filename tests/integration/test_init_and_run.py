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


class TestCheckpointerWiring:
    """Audit follow-up: --checkpointer threads through to graph.py + env + pyproject."""

    def test_no_flag_omits_checkpointer_wiring(self, tmp_path: Path) -> None:
        # Default behaviour: no --checkpointer flag = no get_checkpointer call
        # in the scaffolded graph, no LANGGRAPH_FORGE_CHECKPOINTER_CONN_STRING
        # in env, no [sqlite]/[postgres] extra in pyproject.
        target = tmp_path / "demo_no_cp"
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

        graph_py = (target / "src" / "demo_no_cp" / "graph.py").read_text(encoding="utf-8")
        env_example = (target / ".env.example").read_text(encoding="utf-8")
        pyproject = (target / "pyproject.toml").read_text(encoding="utf-8")

        assert "get_checkpointer" not in graph_py
        assert "CHECKPOINTER_CONN_STRING" not in env_example
        assert "langgraph-forge[sqlite]" not in pyproject
        assert "langgraph-forge[postgres]" not in pyproject

    def test_memory_flag_wires_in_memory_checkpointer(self, tmp_path: Path) -> None:
        target = tmp_path / "demo_mem"
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
                "--checkpointer",
                "memory",
                "--no-input",
            ],
        )
        assert result.exit_code == 0, result.output

        graph_py = (target / "src" / "demo_mem" / "graph.py").read_text(encoding="utf-8")
        env_example = (target / ".env.example").read_text(encoding="utf-8")

        assert 'get_checkpointer("memory")' in graph_py
        # Memory backend needs no conn_string env var.
        assert "CHECKPOINTER_CONN_STRING" not in env_example

    def test_sqlite_flag_wires_sqlite_with_env_and_extra(self, tmp_path: Path) -> None:
        target = tmp_path / "demo_sqlite"
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
                "--checkpointer",
                "sqlite",
                "--no-input",
            ],
        )
        assert result.exit_code == 0, result.output

        graph_py = (target / "src" / "demo_sqlite" / "graph.py").read_text(encoding="utf-8")
        env_example = (target / ".env.example").read_text(encoding="utf-8")
        pyproject = (target / "pyproject.toml").read_text(encoding="utf-8")

        assert 'get_checkpointer("sqlite"' in graph_py
        assert "LANGGRAPH_FORGE_CHECKPOINTER_CONN_STRING" in env_example
        assert "langgraph-forge[sqlite]" in pyproject

    def test_postgres_flag_wires_postgres_with_env_and_extra(self, tmp_path: Path) -> None:
        target = tmp_path / "demo_pg"
        result = runner.invoke(
            app,
            [
                "init",
                str(target),
                "--provider",
                "anthropic",
                "--pattern",
                "router",
                "--deploy",
                "direct",
                "--checkpointer",
                "postgres",
                "--no-input",
            ],
        )
        assert result.exit_code == 0, result.output

        graph_py = (target / "src" / "demo_pg" / "graph.py").read_text(encoding="utf-8")
        env_example = (target / ".env.example").read_text(encoding="utf-8")
        pyproject = (target / "pyproject.toml").read_text(encoding="utf-8")

        assert 'get_checkpointer("postgres"' in graph_py
        assert "LANGGRAPH_FORGE_CHECKPOINTER_CONN_STRING" in env_example
        assert "langgraph-forge[postgres]" in pyproject


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
