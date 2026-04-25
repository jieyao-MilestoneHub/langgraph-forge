# ADR-0006: Ship five multi-agent architectures, sharing one foundation

- **Status**: accepted
- **Date**: 2026-04-25
- **Accepted**: 2026-04-24 — all five architectures shipped (Phases 1-6); foundation symbols, six pattern factories, and the composition recipe are in main.
- **Deciders**: @jieyao-MilestoneHub

## Context

`langgraph-forge` v0.1 shipped a single multi-agent factory,
`create_supervisor_agent`, that was a thin wrapper over
`langgraph_supervisor.create_supervisor`. A user evaluating the package
noted that this "saves no time vs calling upstream directly" and that the
`single` and `supervisor` CLI patterns alone do not cover the multi-agent
topologies LangGraph supports.

The LangChain blog and docs benchmark or recommend five distinct
multi-agent topologies for production use:

1. **Supervisor** — central LLM router
2. **Swarm** — peer-to-peer handoff
3. **Hierarchical** — supervisors over team supervisors
4. **Router + Specialists** — classifier dispatches once, no looping
5. **Custom graph** — user-authored nodes and edges

Each has a different control flow and different performance / governance
trade-offs. A package whose value proposition is "compose, don't
reimplement" must address all five — not by re-inventing them, but by
composing the upstream primitives into a coherent, opinionated CLI +
library surface.

The previous `MultiAgentSpec`-less design also failed the cross-cutting
concerns LangGraph users actually hit: checkpoint strategy, state
reducers, subgraph composition, replay, and human-in-the-loop interrupts.
ADR-0002 captured the deployment-adapter Protocol but said nothing about
multi-agent topology.

## Decision

We ship **five multi-agent architectures plus the existing `single`
pattern** as first-class citizens of both the library API and the
CLI scaffolder, governed by an explicit three-layer boundary that
separates **domain reasoning slots** (where user expertise lives,
in either LLM or encoded form) from **deterministic infrastructure**
(everything else, always built by the framework). They share one
foundation (`MultiAgentSpec`, `SpecialistSpec` with `subgraph`
support, `ThreadConfig`, common reducers, `replay` helper)
so that adding a sixth pattern is one new file, one new
template, one new enum value — zero changes to the existing five.

### The three-layer boundary

This ADR formally adopts the boundary documented in
`docs/explanation/initialization-boundary.md` for the multi-agent
surface specifically:

1. **Reasoning slots** are the only places where domain knowledge
   acts on input. Each pattern's reasoning slots are explicit:
   - Specialist node — every pattern; user picks `(prompt + model
     + tools)` for a live LLM ReAct worker, or `subgraph` for an
     encoded deterministic graph. Both are first-class.
   - Supervisor classifier — `supervisor` and `hierarchical`
     patterns; LLM-only by design (a deterministic supervisor is
     the `custom` pattern's job).
   - Swarm handoff trigger — `swarm` pattern; LLM-only by design.
   - Router classifier — `router` pattern; user picks `ModelSpec`
     (LLM) or `Callable[[State], str]` (encoded code). Both
     first-class.
2. **Infrastructure** (graph topology, typed state channels,
   reducers, tool dispatch, handoff mechanics, persistence,
   static interrupts) is always the framework's deterministic
   Python. A slot's LLM cannot override the topology, skip a
   checkpoint, forge a state update outside its declared channels,
   or talk to another slot directly.
3. **Communication** between slots flows through typed state
   channels, tool calls, and `langgraph.types.Command`. There is
   no message bus, no pub/sub, no unstructured cross-agent
   dictation.

### Architectures

| Name | Routing model | Upstream primitive | Library factory |
|---|---|---|---|
| `single` | One ReAct agent, no orchestration | `langgraph.prebuilt.create_react_agent` | `create_single_agent` |
| `supervisor` | Central LLM decides next step | `langgraph_supervisor.create_supervisor` | `create_supervisor_agent` |
| `swarm` | Active agent hands off to peer | `langgraph_swarm.create_swarm` | `create_swarm_agent` |
| `hierarchical` | Top supervisor over team supervisors | Recursive composition of `create_supervisor_agent` via `SpecialistSpec.subgraph` | `create_hierarchical_agent` |
| `router` | Classifier dispatches once, no loop | Hand-rolled `StateGraph` with conditional edge | `create_router_agent` |
| `custom` | User-authored nodes + edges | `langgraph.graph.StateGraph` | `create_custom_agent` |

### Shared foundation

Lives in `core/specs.py`, `core/reducers.py`, `core/state.py`,
`builders/runtime.py`, `builders/multiagent/_common.py`. These are
exported through `langgraph_forge.__init__.__all__` and locked by
`tests/unit/test_public_api.py`.

| Primitive | Purpose | Used by |
|---|---|---|
| `MultiAgentSpec` | Topology-agnostic config (specialists, state schema, checkpointer, interrupts) | Supervisor / Swarm / Hierarchical / Router |
| `SpecialistSpec.subgraph` | A specialist may be a compiled graph instead of a ReAct worker | Hierarchical (composition payoff) |
| `TeamSpec` | A domain supervisor + its own specialists | Hierarchical |
| `RouterSpec` | A route name + classifier description + target specialist | Router |
| `ThreadConfig` | Frozen dataclass for `thread_id` / `checkpoint_ns` / `checkpoint_id` | All factories (via runtime helpers) |
| `merge_dict_reducer`, `append_unique_reducer` | Custom state-channel merge functions LangGraph does not ship | User extensions of `ForgeState` |
| `replay` | Re-run from checkpoint, optional state-modification fork | All factories |

### CLI surface

`Pattern` enum extends from 2 to 6 values:

```
langgraph-forge init my-app --pattern <single|supervisor|swarm|hierarchical|router|custom> ...
```

Each value resolves to a builder factory in `builders/multiagent/`
(or `builders/single.py`) and a template directory in
`scaffold/templates/patterns/<name>/`. Adding a seventh pattern is
mechanical: one factory file, one template directory, one enum
value, one ADR.

### Cross-cutting concerns answered

- **Checkpoint**: `MultiAgentSpec.checkpointer`, plus `ThreadConfig`
  for the `{"configurable": {"thread_id": ...}}` dict shape.
- **Reducer**: `core/reducers.py` ships the two non-trivial reducers
  (merge-dict, append-unique). Trivial cases use upstream
  `add_messages` or `operator.add`.
- **Subgraph**: `SpecialistSpec.subgraph` lets any compiled
  `CompiledStateGraph` slot in as a specialist. Hierarchical is
  literally a recursive use of this.
- **Replay**: `replay(graph, thread, modify=None)` wraps the
  `graph.invoke(None, config={"configurable": {"thread_id": ...,
  "checkpoint_id": ...}})` idiom. `modify` triggers
  `graph.update_state` first for a counterfactual fork.
- **Interrupt**: every factory accepts `interrupt_before` /
  `interrupt_after` lists of node names. To continue after a pause,
  use upstream `Command(resume=value)` directly — see
  `docs/how-to/resume-after-interrupt.md` for the recipe. Dynamic
  in-node `interrupt(...)` is not wrapped — users import directly
  from `langgraph.types`.

## Consequences

**Positive:**

- The CLI matrix (provider × pattern × deploy) finally pulls weight
  on the `pattern` axis. Six patterns covers every topology the
  LangGraph blog benchmarks.
- Adding the sixth pattern was the **last** time the codebase
  needed structural change. Future patterns are pure additions.
- The composition-not-reimplementation invariant is preserved: each
  factory is a 30-line wrapper over upstream + shared `_common.py`
  worker construction.
- Hierarchical demonstrates the `subgraph` field's payoff: a complex
  topology with **zero new code** beyond a 30-line factory that
  recursively calls supervisor.

**Negative:**

- 10 new public symbols (`MultiAgentSpec`, `TeamSpec`, `RouterSpec`,
  `ThreadConfig`, two reducers, `replay`, three new factories;
  `resume` was added in 0.2.0a1 and dropped in 0.3.0a1 per the
  trade-off audit). The public API stability test now locks 30
  names. This is an intentional commitment; future drift surfaces
  as a test diff.
- Breaking change to `create_supervisor_agent` signature (now takes
  `MultiAgentSpec` not loose kwargs). Pre-1.0 minor bump
  (`0.1.x → 0.2.0`) per VERSIONING.md § B.
- Documentation surface grows: each pattern needs explanation +
  reference + a how-to. Seeded as placeholders, filled as users ask.

**Neutral:**

- `langgraph-swarm` becomes a runtime dependency. Lightweight, no
  cloud SDK, but increases the install footprint marginally.

## Alternatives considered

- **Ship only supervisor + swarm + pipeline (3 patterns)**: rejected.
  Pipeline is a degenerate case of router (no LLM classifier);
  hierarchical is high-value for enterprise use cases LangChain blog
  explicitly calls out.
- **Build all five from scratch without `langgraph-supervisor` /
  `langgraph-swarm`**: rejected. Violates the
  composition-not-reimplementation invariant. Maintenance cost would
  re-create what the upstream packages already test.
- **Single dispatching factory `create_multi_agent(pattern=...)`**:
  rejected. Hides the pattern-specific kwargs (supervisor needs
  prompt, swarm needs default_active, router needs classifier) under
  `**kwargs` or a polymorphic spec. Dedicated factories are clearer
  contracts and easier to type-check.
- **Treat `custom` as a doc page, not a factory**: rejected. Users
  asking for `--pattern custom` deserve a scaffolded entry point
  even if our factory is 10 lines over `StateGraph`.

## See also

- [`docs/explanation/multi-agent-architectures.md`](../../explanation/multi-agent-architectures.md)
  — the user-facing explanation of when to pick which pattern.
- [`docs/explanation/initialization-boundary.md`](../../explanation/initialization-boundary.md)
  § "The package's job" — these factories qualify under
  "compose LangGraph primitives" + "scaffold a runnable starting
  point".
- ADR-0002 (DeploymentAdapter Protocol shape) — the deploy surface
  uses the same SOLID extension pattern this ADR adopts for patterns.
