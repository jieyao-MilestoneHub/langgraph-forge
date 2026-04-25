"""Typer CLI exposing the scaffolder."""

from __future__ import annotations

import importlib
from enum import StrEnum
from pathlib import Path

import typer

from langgraph_forge._version import __version__
from langgraph_forge.deploy.registry import discover_adapters
from langgraph_forge.scaffold.render import render_project

app = typer.Typer(
    name="langgraph-forge",
    help="Initialise LangGraph-based agent architectures.",
    no_args_is_help=True,
    add_completion=False,
)


class Provider(StrEnum):
    """LLM providers the scaffolder knows how to wire."""

    anthropic = "anthropic"
    openai = "openai"
    grok = "grok"
    google = "google"
    bedrock = "bedrock"
    azure = "azure"


class Pattern(StrEnum):
    """Agent execution patterns the scaffolder offers."""

    single = "single"
    supervisor = "supervisor"
    swarm = "swarm"
    hierarchical = "hierarchical"
    router = "router"


# ---------------------------------------------------------------------------
# Listing commands (stateless, safe for CI)
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Print the installed langgraph-forge version."""
    typer.echo(__version__)


@app.command("list-providers")
def list_providers() -> None:
    """List supported LLM providers."""
    for p in Provider:
        typer.echo(p.value)


@app.command("list-patterns")
def list_patterns() -> None:
    """List supported execution patterns."""
    for p in Pattern:
        typer.echo(p.value)


@app.command("list-deploy")
def list_deploy() -> None:
    """List every registered deployment adapter (first- and third-party)."""
    for name, cls in sorted(discover_adapters().items()):
        extras = ",".join(cls.requires_extras) or "-"
        suffix = "  (stub — runtime planned for v0.2)" if getattr(cls, "is_stub", False) else ""
        typer.echo(f"{name}  extras={extras}{suffix}")


@app.command()
def doctor(
    deploy: str = typer.Option(..., "--deploy", help="Deployment adapter to check"),
) -> None:
    """Verify that an adapter's optional extras are installed."""
    adapters = discover_adapters()
    if deploy not in adapters:
        typer.echo(f"Unknown adapter: {deploy!r}. Run list-deploy to see options.")
        raise typer.Exit(code=1)

    cls = adapters[deploy]
    missing = []
    for extra in cls.requires_extras:
        module_name = extra.replace("-", "_")
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(extra)

    if missing:
        typer.echo(f"Adapter {deploy!r} needs: {', '.join(missing)}")
        typer.echo(f"Install with: pip install langgraph-forge[{deploy}]")
        raise typer.Exit(code=1)

    typer.echo(f"Adapter {deploy!r} is ready.")


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


_TEMPLATE_ROOT = Path(__file__).parent / "templates"


# typer requires the Argument()/Option() *call* in defaults so it can build
# the CLI metadata at decoration time; B008's "no function call in defaults"
# does not apply here. Suppressed locally rather than globally so accidental
# B008 elsewhere still trips review.
@app.command()
def init(
    target: Path = typer.Argument(..., help="Target project directory to create."),  # noqa: B008
    provider: Provider = typer.Option(..., "--provider"),  # noqa: B008
    pattern: Pattern = typer.Option(..., "--pattern"),  # noqa: B008
    deploy: str = typer.Option(..., "--deploy"),
    mcp: Path | None = typer.Option(None, "--mcp", help="Path to MCP config JSON"),  # noqa: B008
    no_input: bool = typer.Option(False, "--no-input"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    """Scaffold a new agent project."""
    adapters = discover_adapters()
    if deploy not in adapters:
        typer.echo(f"Unknown adapter: {deploy!r}. Run list-deploy to see options.")
        raise typer.Exit(code=1)

    adapter_cls = adapters[deploy]

    if getattr(adapter_cls, "is_stub", False):
        typer.echo(
            f"Note: adapter {deploy!r} is a v0.2-planned stub. The scaffolded "
            f"deploy.py will import successfully and graph compilation works, "
            f"but ADAPTER.prepare()/invoke() raises NotImplementedError until "
            f"the runtime ships. Use --deploy direct for a fully functional "
            f"reference.",
            err=True,
        )

    sources = [
        _TEMPLATE_ROOT / "base",
        _TEMPLATE_ROOT / "patterns" / pattern.value,
        _TEMPLATE_ROOT / "providers" / provider.value,
        adapter_cls().template_fragment(),
    ]

    context = {
        "project_name": target.name,
        "package_name": target.name.replace("-", "_"),
        "provider": provider.value,
        "pattern": pattern.value,
        "deploy": deploy,
        "mcp_path": str(mcp) if mcp else "",
    }

    render_project(
        target_dir=target,
        template_sources=sources,
        context=context,
        overwrite=force,
    )

    typer.echo(f"Project scaffolded at {target}")
