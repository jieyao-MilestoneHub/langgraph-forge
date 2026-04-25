# ADR-0002: DeploymentAdapter Protocol shape

- **Status**: accepted
- **Date**: 2026-04-25
- **Deciders**: @jieyao-MilestoneHub

## Context

The project must let users target multiple deployment runtimes —
local self-hosted (Direct), AWS Bedrock AgentCore, GCP Vertex Agent
Engine, Azure AI Agent Service — and let third parties add new
targets without modifying the core. The common thread across all
four is "given a compiled `langgraph` graph, prepare a deployable
artifact and invoke it with inputs"; the differences are in
authentication, registration, and per-target options (region,
project, endpoint, agent id, session identity).

We needed a contract that is:

1. Small enough that authoring a new adapter is mechanical.
2. Expressive enough that vendor-specific knobs (Bedrock session
   identity, Vertex location, Azure endpoint) live somewhere
   sensible.
3. Lazy about cloud SDK imports so `pip install langgraph-forge`
   without extras stays light.
4. Discoverable so third-party adapters can register without an
   upstream PR.

## Decision

`DeploymentAdapter` is a **`runtime_checkable` Protocol** with five
members, defined at `src/langgraph_forge/deploy/base.py`:

```python
@runtime_checkable
class DeploymentAdapter(Protocol):
    name: str
    requires_extras: tuple[str, ...]
    def prepare(self, graph: Any, config: AdapterConfig) -> Any: ...
    async def invoke(self, deployable: Any, inputs: dict) -> dict: ...
    def template_fragment(self) -> Path: ...
```

Companion dataclass:

```python
@dataclass(frozen=True)
class AdapterConfig:
    project_name: str
    extra: dict[str, Any] = field(default_factory=dict)
```

**Key shape choices:**

- **`AdapterConfig.extra: dict[str, Any]`** absorbs all
  vendor-specific options. Bedrock's `region`, Vertex's `location`,
  Azure's `endpoint` go in `extra`, not on the Protocol. This is
  Interface Segregation: the Protocol does not force concepts from
  one adapter onto the others.
- **Cloud SDKs imported lazily** inside `prepare()` (or `invoke()`),
  not at module level. `pip install langgraph-forge` (no extras)
  keeps every adapter module importable; the SDK only loads if the
  user actually invokes the adapter.
- **Discovery via `importlib.metadata` entry points** under the
  `langgraph_forge.deployment_adapters` group. Third parties publish
  `langgraph-forge-modal` or similar with their own adapter class
  + entry point; `langgraph-forge list-deploy` and the scaffolder's
  `--deploy modal` flag pick it up automatically.
- **`template_fragment()` returns a Path** to a directory under
  `src/langgraph_forge/scaffold/templates/deploy_fragments/<name>/`.
  Each adapter ships its own `deploy.py.j2` template fragment; the
  scaffold renderer composes it on top of base + pattern + provider
  layers.

## Consequences

**Positive:**

- Adding a fifth adapter is a zero-diff change to core: a new
  package satisfies the Protocol, declares an entry point, ships
  a template fragment.
- The Protocol type-checks structurally, so adapter authors do not
  need to inherit from anything; duck-typed conformance is enough.
- Cloud SDK install footprint is opt-in; `pip install
  langgraph-forge[bedrock]` only matters when users target Bedrock.
- Third-party adapters can ship without a fork or upstream PR.

**Negative:**

- `AdapterConfig.extra` is `dict[str, Any]` — opaque to type
  checkers. Adapter authors carry the validation burden inside
  their own `prepare()`. Mitigated by adapter-level docstrings
  enumerating the keys they consume.
- The five-member Protocol is the smallest contract that supports
  CLI scaffolding (template_fragment) + extras-checking
  (requires_extras) + execution (prepare / invoke). Adapters that
  only execute (no CLI integration) still implement
  `template_fragment` — for those, returning a path that does not
  exist is acceptable; the renderer skips missing sources.

**Neutral:**

- `runtime_checkable` adds a small overhead to `isinstance()` calls.
  We use it in `discover_adapters` for shape-validation only, not in
  hot paths.

## Alternatives considered

- **Abstract base class**: rejected. Forces inheritance, couples
  third-party adapters to importing our core class at definition
  time. Protocol gives us the same shape check without the import.
- **Single function `def deploy(graph, config) -> Any`**: rejected.
  The split between `prepare` (one-time registration) and `invoke`
  (per-request) is real for cloud targets; collapsing it forces
  every invoke to re-register.
- **Bedrock-shaped Protocol** (e.g., a `region` parameter): rejected
  per Interface Segregation; would force every adapter to carry
  fields it does not need.
- **Plugin manifest file** (e.g., `langgraph_forge_plugins.toml`):
  rejected. Entry points are the Python ecosystem's native plugin
  mechanism; adopting a parallel system raises the bar for
  contributors.

## See also

- `src/langgraph_forge/deploy/base.py` — the Protocol source.
- `src/langgraph_forge/deploy/registry.py` — entry-point discovery.
- [`../repository-tour.md`](../repository-tour.md) § `deploy/`.
- [`/CONTRIBUTING.md`](../../../CONTRIBUTING.md) — adapter
  contribution playbook (in-tree and out-of-tree).
