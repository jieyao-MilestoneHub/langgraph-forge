# Initialization boundary

This page is the charter for what `langgraph-forge` does, what it
deliberately does not do, and how to tell the difference. Read this
before adding a new public symbol; refer to it during PR review when
asking "is this in scope?".

## The package's job

The package's value proposition is **"compose, don't reimplement"**.
Every public symbol earns its place by doing one of these and only
these:

1. **Standardise a config shape**. Frozen Pydantic specs
   (`ModelSpec`, `SpecialistSpec`, `MCPConfig`, `MCPServerConfig`)
   replace ad-hoc dicts with one diffable, version-controllable type
   per concern.
2. **Compose LangGraph primitives**. The supervisor factory wires
   `SpecialistSpec[]` → ReAct workers → `langgraph_supervisor.create_supervisor`
   → `compile()` in one call. That's the line-saving part.
3. **Unify the import surface**. `get_model`, `create_single_agent`,
   `load_mcp_tools`, `get_checkpointer` are deliberately thin, but
   they save users from learning three to five upstream package paths
   for the same task. The value is consistency more than line count.
4. **Provide an extension contract**. The
   [`DeploymentAdapter`](../../src/langgraph_forge/deploy/base.py)
   Protocol and the
   `langgraph_forge.deployment_adapters` entry-point group let third
   parties plug in deployment targets without a fork.
5. **Scaffold a runnable starting point**. The CLI generates a
   project that compiles, has tests, and can be `python -m`'d
   without touching package internals.

If a proposed symbol does none of the above, it does not belong here.

## The user's job

The package gives you a frame; it does not write the agent.

Things that are explicitly **your code**, not the package's:

- **Tools** — `BaseTool` instances or callables decorated with
  `@tool`. `langgraph-forge` has no opinion on what your agent can
  do; it just hands the list to the underlying ReAct factory.
- **Prompts** — supervisor prompts and per-specialist prompts are
  strings you author. The scaffolded templates ship two example
  specialists (`researcher`, `summariser`) but those are
  illustrative, not normative.
- **Domain validation** — output schemas, tool allowlists, retry
  policies, circuit breakers, rate limits. Layer them on top of the
  factories; we will not bake them in.
- **Observability** — LangSmith, OpenTelemetry, custom callbacks.
  The compiled graph from any factory accepts the LangChain callback
  pattern; wire it yourself.
- **Authentication / authorisation / multi-tenancy / billing** — out
  of scope, full stop. If the package starts knowing about user
  identities or quota buckets, the boundary is broken.
- **Streaming behaviour** — `graph.astream(...)` is already the
  answer. We will not ship a streaming helper; it would be a thinner
  wrapper than `get_model` and earn even less.

## The package will never do these

These are **permanent** anti-scope items. PRs proposing them will be
closed without review:

- HTTP / REST / WebSocket / SSE serving
- Authentication, authorisation, permission management
- Rate limiting, quota enforcement, billing
- Web UI / dashboard
- Prompt versioning, prompt registry, content-hash-based prompt cache
- Output-envelope validation, schema registry
- Eval harness, scoring, metric aggregation
- Tool allowlists, side-effect gates, autonomy gates,
  budget / cost ceilings, cycle detection
- Peer review, human review queue, exception ticket routing
- Direct integration with vector stores, document loaders, or RAG
  components — those are LangChain's territory
- Translations / i18n of the package or templates

If you need any of these, build them on top of `langgraph-forge` —
they will not move into it.

## Why some wrappers are so thin

`get_model` is six lines. `create_single_agent` is nine. The honest
answer to "why is this even a function?":

1. **One canonical import path**. A user writes
   `from langgraph_forge import ...` once. Without these wrappers
   they'd write three to five upstream imports per file
   (`from langchain.chat_models import init_chat_model`,
   `from langgraph.prebuilt import create_react_agent`,
   `from langchain_core.tools import BaseTool`, …).
2. **A future hook point**. If we ever need to add cross-cutting
   behaviour (default retry, telemetry hook, prompt-cache marker),
   the wrappers are the place. Putting them in users' code paths
   from day one means the upgrade is non-breaking.
3. **A ModelSpec / SpecialistSpec audit trail**. When you read
   `get_model(spec)` in user code, you can git-blame `spec` to a
   declaration. When you read `init_chat_model(...)` with literal
   args inline, you can't.

If, six months in, none of these reasons holds — delete the wrapper
and re-export the upstream function. We are not married to thin
wrappers; we are married to one canonical import and one config
audit trail.

## Multi-MCP-server scenarios — where to outgrow this

`load_mcp_tools(MCPConfig)` and `MCPServerConfig` cover the
straightforward "I have N MCP servers; give me their tools as a flat
list" case. That's deliberately the only MCP capability we ship.

If you need **more** — registry-style server discovery, lifecycle
management across many servers, cross-server dependency wiring, hot
reload, fine-grained tool routing — look at
[`mcp-forge-core`](https://pypi.org/project/mcp-forge-core/) on
PyPI. It's a separate package with a deeper feature set for exactly
those scenarios.

The `MCPConfig` shape we ship is intentionally compatible with the
underlying
[`langchain-mcp-adapters`](https://pypi.org/project/langchain-mcp-adapters/)
dict format, so migrating to or from it later is a flat-translation,
not a rewrite.

## How to tell if a proposed addition is in scope

Three questions, in order. A "no" anywhere short-circuits to "not in
scope; user code or another package".

1. **Does it standardise a config shape, compose LangGraph
   primitives, unify the import surface, provide an extension
   contract, or scaffold a runnable starting point?** (See "The
   package's job".) If no, stop.
2. **Is it provider-agnostic, pattern-agnostic, and
   deployment-agnostic?** A symbol that only makes sense for one
   provider, one pattern, or one deployment is somebody's adapter
   or template — not a core public symbol.
3. **Does it avoid every item in "The package will never do
   these"?** If it touches HTTP, auth, prompt versioning, eval,
   observability, etc., it does not land here.

## Test-driven boundary

The public API is locked by
[`tests/unit/test_public_api.py`](../../tests/unit/test_public_api.py).
Adding or removing a symbol from `langgraph_forge.__init__.__all__`
is a test diff that forces a review checkpoint. The test is
deliberately simple — it asserts the exact set of exported names
matches a hardcoded list — so it does not bit-rot, but it does ring
a bell every time the surface changes.

## See also

- [`/CONTRIBUTING.md`](../../CONTRIBUTING.md) §
  "What's out of scope" — the contributor-side checklist.
- [`/VERSIONING.md`](../../VERSIONING.md) § B — what counts as a
  public symbol for breaking-change purposes.
- ADRs in [`../contributing/decisions/`](../contributing/decisions/README.md)
  — historical record of where boundaries were drawn.
