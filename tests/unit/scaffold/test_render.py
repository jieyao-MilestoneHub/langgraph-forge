"""Tests for langgraph_forge.scaffold.render."""

from __future__ import annotations

from pathlib import Path

import pytest

from langgraph_forge.scaffold.render import render_project


@pytest.fixture
def simple_source(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    (src / "greeting.txt.j2").write_text("Hello {{ name }}!\n", encoding="utf-8")
    (src / "static.md").write_text("# Static file\n", encoding="utf-8")
    subdir = src / "sub"
    subdir.mkdir()
    (subdir / "nested.py.j2").write_text("PROVIDER = '{{ provider }}'\n", encoding="utf-8")
    return src


class TestJinjaRendering:
    def test_j2_file_rendered_with_context(
        self, simple_source: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "out"
        render_project(
            target_dir=target,
            template_sources=[simple_source],
            context={"name": "forge", "provider": "anthropic"},
        )

        assert (target / "greeting.txt").read_text(encoding="utf-8") == "Hello forge!\n"

    def test_j2_suffix_stripped_from_output_filename(
        self, simple_source: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "out"
        render_project(
            target_dir=target,
            template_sources=[simple_source],
            context={"name": "forge", "provider": "anthropic"},
        )

        assert not (target / "greeting.txt.j2").exists()

    def test_nested_directories_preserved(
        self, simple_source: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "out"
        render_project(
            target_dir=target,
            template_sources=[simple_source],
            context={"name": "forge", "provider": "anthropic"},
        )

        assert (
            target / "sub" / "nested.py"
        ).read_text(encoding="utf-8") == "PROVIDER = 'anthropic'\n"


class TestStaticCopy:
    def test_non_j2_file_copied_verbatim(
        self, simple_source: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "out"
        render_project(
            target_dir=target,
            template_sources=[simple_source],
            context={"name": "forge", "provider": "anthropic"},
        )

        assert (target / "static.md").read_text(encoding="utf-8") == "# Static file\n"


class TestOverwriteGuard:
    def test_non_empty_target_without_overwrite_raises(
        self, simple_source: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "out"
        target.mkdir()
        (target / "existing.txt").write_text("already here", encoding="utf-8")

        with pytest.raises(FileExistsError, match="target"):
            render_project(
                target_dir=target,
                template_sources=[simple_source],
                context={"name": "x", "provider": "y"},
            )

    def test_non_empty_target_with_overwrite_succeeds(
        self, simple_source: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "out"
        target.mkdir()
        (target / "existing.txt").write_text("already here", encoding="utf-8")

        render_project(
            target_dir=target,
            template_sources=[simple_source],
            context={"name": "x", "provider": "y"},
            overwrite=True,
        )

        assert (target / "greeting.txt").exists()


class TestReturnValue:
    def test_returns_list_of_written_paths(
        self, simple_source: Path, tmp_path: Path
    ) -> None:
        target = tmp_path / "out"

        written = render_project(
            target_dir=target,
            template_sources=[simple_source],
            context={"name": "x", "provider": "y"},
        )

        assert {p.name for p in written} == {"greeting.txt", "static.md", "nested.py"}
