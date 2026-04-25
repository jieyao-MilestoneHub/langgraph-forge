# Repository tour

A one-page map of the codebase. Use this when you need to know where
something lives or where new code should go.

## Top-level layout

```
langgraph-forge/
├── src/langgraph_forge/   # The package (everything shipped to PyPI)
├── tests/                 # Unit + integration tests, mirroring src/
├── docs/                  # Documentation (you are here)
├── .github/               # GitHub config: workflows, templates, labels
├── .claude/               # AI tooling config: rules, agents, skills
├── pyproject.toml         # Build, deps, ruff/pyright/pytest config
├── cliff.toml             # git-cliff release-notes template
├── README.md              # PyPI / GitHub landing page
├── CONTRIBUTING.md        # Contribution flow entry point
├── MAINTAINERS.md         # Maintainer ops entry point
├── VERSIONING.md          # Release semantics
├── SECURITY.md            # Vulnerability disclosure
└── LICENSE                # MIT
```

## `src/langgraph_forge/` — four subpackages, one direction

The dependency direction is strict: `scaffold/` → `deploy/` →
`builders/` → `core/`. No subpackage imports from a sibling later in
this list. A cycle would surface immediately when you try to add it.

### `core/` — value objects + shared types

Pure data and exception types. No factories, no graph construction,
no upstream LangGraph imports for behaviour (only types).

| File | What's in it |
|---|---|
| `state.py` | `ForgeState` TypedDict — `messages` channel + `add_messages` reducer. Users subclass to extend. |
| `specs.py` | Frozen Pydantic models: `ModelSpec`, `SpecialistSpec`, `MCPConfig`, `MCPServerConfig`. |
| `errors.py` | `ForgeError` (base), `ForgeConfigError`, `MissingExtraError`. |

### `builders/` — runtime factories (the core library value)

Thin compositions of LangGraph / LangChain / MCP primitives. Every
function takes a `core.specs` value and produces a runtime object.

| File | What's in it |
|---|---|
| `llm.py` | `get_model(spec: ModelSpec) -> BaseChatModel`. Six-line wrap of `langchain.chat_models.init_chat_model`. |
| `single.py` | `create_single_agent(...)`. Wraps `langgraph.prebuilt.create_react_agent`. |
| `supervisor.py` | `create_supervisor_agent(...)`. Wraps `langgraph_supervisor.create_supervisor`, lifting `SpecialistSpec` instances into ReAct workers. |
| `mcp.py` | `load_mcp_tools(config: MCPConfig)`. Async wrap of `langchain_mcp_adapters.MultiServerMCPClient`. |
| `checkpoint.py` | `get_checkpointer(kind, **kwargs)`. Lazy-imports per backend (memory / sqlite / postgres). |

### `deploy/` — ports + adapters (hexagonal)

The `DeploymentAdapter` Protocol is the port; concrete classes are
the adapters. Cloud SDKs are imported lazily inside `prepare()` so
`pip install langgraph-forge` (no extras) leaves all adapters
importable.

| File | What's in it |
|---|---|
| `base.py` | `DeploymentAdapter` Protocol + `AdapterConfig` dataclass. The Protocol is the public contract. |
| `direct.py` | `DirectAdapter` — fully implemented. `prepare` returns the graph; `invoke` awaits `graph.ainvoke`. |
| `bedrock.py` | `BedrockAgentCoreAdapter` — Protocol-conformant stub (`prepare`/`invoke` raise `NotImplementedError("v0.2")`). |
| `vertex.py` | `VertexAgentEngineAdapter` — same shape. |
| `azure.py` | `AzureAIAgentAdapter` — same shape. |
| `registry.py` | `discover_adapters()` / `get_adapter(name)` via `importlib.metadata` entry points. |

### `scaffold/` — CLI + templates (dev-time)

Everything users only run via `langgraph-forge` on the command line.
Cloud SDKs never get pulled in here either; `cli.py`'s `doctor` does
optional `importlib.import_module` probing without forcing the
extras.

| File | What's in it |
|---|---|
| `cli.py` | Typer app: `init` / `list-providers` / `list-patterns` / `list-deploy` / `doctor` / `version`. |
| `render.py` | Jinja2 renderer with path-segment substitution (`src/{{ package_name }}/...`). |
| `templates/` | The template stack — `base/`, `patterns/{single,supervisor}/`, `providers/{anthropic,openai,grok,google,bedrock,azure}/`, `deploy_fragments/{direct,bedrock,vertex,azure}/`. |

### Public facade — `src/langgraph_forge/__init__.py`

The 17 symbols re-exported here are the **only** stable surface. Anything
not in `__all__` is internal and may move between subpackages without
notice. See [`/VERSIONING.md`](../../VERSIONING.md) § B for the
breaking-change rule.

## `tests/` — mirrors `src/`

```
tests/
├── unit/
│   ├── core/
│   ├── builders/
│   ├── deploy/
│   └── scaffold/
└── integration/
    └── test_init_and_run.py
```

Unit tests mock at the **library boundary** (`init_chat_model`,
`MultiServerMCPClient.get_tools`, cloud SDK imports). LangGraph's own
factories (`create_react_agent`, `create_supervisor`) are called for
real because they're our dependency, not our system boundary. See
[`testing.md`](./testing.md) for the full mock discipline.

## `docs/` — split by audience and Diátaxis quadrant

Already documented at [`docs/README.md`](../README.md). User docs
under `tutorials/`, `how-to/`, `reference/`, `explanation/`; developer
docs here under `contributing/`; maintainer docs under `governance/`.

## `.github/` — GitHub-specific config

| Path | What's in it |
|---|---|
| `workflows/ci.yml` | Matrix lint/type/test on push to `main` and on every PR. |
| `workflows/publish.yml` | Tag-triggered build → OIDC publish to PyPI → git-cliff release notes. |
| `ISSUE_TEMPLATE/*.yml` | Bug, feature, provider, adapter forms. |
| `PULL_REQUEST_TEMPLATE.md` | PR checklist (TDD evidence, four check categories, quality gates). |
| `dependabot.yml` | Weekly grouped pip + GitHub Actions updates. |
| `CODEOWNERS` | Default `@jieyao-MilestoneHub`; release-critical files require explicit review. |
| `labels.yml` | Source of truth for the project's label set. |

## `.claude/` — AI tooling config (not a contribution surface)

`.claude/rules/` carries the project's engineering invariants in a
form that AI sessions can ingest at conversation start. Human
contributors get the same rules through this docs/ tree, the linked
`CONTRIBUTING.md` / `MAINTAINERS.md`, and the references in PR
templates. The two surfaces stay aligned by hand; if you change a rule
in one place, mirror it in the other.

## See also

- [`testing.md`](./testing.md) — how the test suite is organised and
  what's mocked where.
- [`decisions/`](./decisions/README.md) — the ADRs that explain why
  this layout (and not a flat src layout, or a separate docs repo).
