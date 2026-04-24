"""Jinja2-based project renderer for the CLI ``init`` command."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


def render_project(
    *,
    target_dir: Path,
    template_sources: list[Path],
    context: dict[str, Any],
    overwrite: bool = False,
) -> list[Path]:
    """Render a stack of template directories into ``target_dir``.

    Every source in ``template_sources`` is walked in order (later
    sources overwrite earlier ones on file-name collisions, so a
    deployment adapter's ``deploy.py.j2`` can override the base
    ``deploy.py.j2`` if one exists).

    Files ending in ``.j2`` are rendered through Jinja2 with
    ``context`` as the variable environment; every other file is
    copied byte-for-byte. The ``.j2`` suffix is stripped from the
    output filename.

    The target directory is created if missing. If it exists and is
    non-empty, ``overwrite=True`` is required to proceed -- this is
    the guard between ``langgraph-forge init existing_dir`` and data
    loss.
    """
    if target_dir.exists() and any(target_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"target {target_dir} already exists and is non-empty; pass "
            "overwrite=True to render into it anyway."
        )
    target_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for source in template_sources:
        if not source.exists():
            continue
        written.extend(_render_source(source, target_dir, context))
    return written


def _render_source(
    source: Path, target_dir: Path, context: dict[str, Any]
) -> list[Path]:
    env = Environment(
        loader=FileSystemLoader(source),
        keep_trailing_newline=True,
        autoescape=False,  # we render source code, not HTML
    )
    written: list[Path] = []
    for rel_path in _walk_files(source):
        src_file = source / rel_path
        if rel_path.suffix == ".j2":
            template = env.get_template(rel_path.as_posix())
            content_str = template.render(**context)
            dest = target_dir / rel_path.with_suffix("")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content_str, encoding="utf-8")
        else:
            dest = target_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src_file.read_bytes())
        written.append(dest)
    return written


def _walk_files(root: Path) -> list[Path]:
    return sorted(
        p.relative_to(root) for p in root.rglob("*") if p.is_file()
    )
