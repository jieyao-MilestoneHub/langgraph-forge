# Multi-agent architectures

`langgraph-forge` ships **six** scaffold patterns. One is the
single-agent baseline; the other five are distinct multi-agent
topologies. This page explains when to pick which one and why we
ship them as separate factories rather than as a single configurable
function.

## Before reading: the boundary

Every pattern below honours the same three-layer boundary
([initialization-boundary.md](./initialization-boundary.md) §
"The principle"):

- **Reasoning slots** (specialist nodes, supervisor classifier,
  router classifier) hold the domain expertise. Each slot accepts
  **either** a live LLM (the default — ReAct or classifier model)
  **or** encoded deterministic code (`SpecialistSpec.subgraph`, a
  `Callable` classifier). The package never bakes domain assumptions
  into a slot.
- **Infrastructure** (graph topology, typed state channels, reducers,
  tool dispatch, handoff mechanics, persistence, static interrupts)
  is always the framework's deterministic Python. A slot's LLM never
  overrides the topology or forges state updates outside declared
  channels.
- **Communication** between slots flows through typed state, tool
  calls, or `Command` — never free-form prose passed by name.

Read the boundary doc first if any of these are unclear; the patterns
below are concrete instantiations of that abstract contract.

## At a glance

| Pattern | Routing | Best for | Trade-off |
|---|---|---|---|
| `single` | None | One ReAct agent with tools; baseline | No specialisation |
| `supervisor` | Central LLM decides next step | Most general-purpose; corporate workflows; explicit orchestration | Supervisor LLM call every turn |
| `swarm` | Active agent hands off to peer | Conversational, agent-to-agent flows; lower token cost | Agents must know each other; harder to govern |
| `hierarchical` | Top supervisor over team supervisors | Large systems with clear domains (support team → billing/tech/refunds) | Two LLM hops per delegation |
| `router` | Classifier picks one specialist, no loop | Crisp task taxonomy; one-shot dispatch | Cannot revisit if first specialist underperforms |
| `custom` | User-authored | Production workflows mixing deterministic code, parallel execution, conditional branching | You write the graph |

If you have to pick one to start with, **start with `supervisor`**.
LangChain's own benchmarking found supervisor makes the fewest
assumptions and adapts to most multi-agent use cases. Graduate to
hierarchical if your domain decomposes into teams; graduate to swarm
if you want lower per-turn token cost and your agents have clear
"I'm done, your turn" signals.

## When to pick which

### Supervisor

A central LLM reads the conversation, decides which specialist to
call next, calls it, and incorporates the result. The supervisor's
own reasoning is visible in the trace, so debugging "why did it pick
X?" is easy.

```python
from langgraph_forge import (
    MultiAgentSpec, SpecialistSpec, ModelSpec,
    create_supervisor_agent, get_model,
)

spec = MultiAgentSpec(
    specialists=[
        SpecialistSpec(name="researcher", prompt="...", model=ModelSpec(...)),
        SpecialistSpec(name="writer",     prompt="...", model=ModelSpec(...)),
    ],
)
graph = create_supervisor_agent(
    spec,
    supervisor_model=get_model(ModelSpec(model="claude-opus-4-7", provider="anthropic")),
    supervisor_prompt="You orchestrate research and writing.",
)
```

### Swarm

Each agent gets a `transfer_to_<peer>` handoff tool. The active agent
is part of state and updates whenever a handoff fires. Useful when
agents have natural conversational pivots ("now let's hand to the
booking agent").

```python
from langgraph_forge import create_swarm_agent

graph = create_swarm_agent(
    spec,
    default_active_agent="triage",
)
```

### Hierarchical

A `TeamSpec` describes a domain supervisor with its own specialists.
The top-level supervisor's "specialists" are these team subgraphs.
The composition is recursive — each team is itself a supervisor
graph, slotted in via `SpecialistSpec.subgraph`. **No new code path:**
the hierarchical factory just calls `create_supervisor_agent`
multiple times.

```python
from langgraph_forge import TeamSpec, create_hierarchical_agent

teams = [
    TeamSpec(
        name="billing",
        supervisor_model=ModelSpec(...),
        supervisor_prompt="Resolve billing tickets.",
        specialists=[SpecialistSpec(name="invoice_lookup", ...), ...],
    ),
    TeamSpec(name="tech_support", ...),
]
graph = create_hierarchical_agent(
    top_supervisor_model=...,
    top_supervisor_prompt="Route customers to the right team.",
    teams=teams,
)
```

### Router + Specialists

A classifier — either a small LLM or a deterministic function — picks
the specialist for this request. The chosen specialist runs once;
optionally a synthesis step combines outputs. There is no loop back
to the classifier.

Use this when your task taxonomy is crisp (refund vs. tech-support vs.
sales) and you do not need the supervisor's iterative re-routing.
Cheaper than supervisor for one-shot classifications.

### Custom

When you need parallel execution, conditional branching, deterministic
nodes mixed with LLM nodes, or anything else the prebuilt patterns do
not give you, drop down to LangGraph's `StateGraph` directly.
`create_custom_agent` is a thin builder that takes a state schema, a
dict of nodes, and a list of edges, and returns a compiled graph. The
escape hatch is documented, not hidden.

## What's shared across all five multi-agent patterns

This is the "no rework" foundation. Every pattern reads from these
without re-implementing:

- **`MultiAgentSpec`** — list of specialists, the state schema, the
  checkpointer, and `interrupt_before` / `interrupt_after` node lists.
  Every multi-agent factory takes one. Pattern-specific extras
  (supervisor prompt, default active agent, router classifier) ride
  as kwargs to the factory, not as fields on the spec.
- **`SpecialistSpec.subgraph`** — a specialist may be a compiled
  graph instead of a ReAct worker. Hierarchical exploits this.
- **`ThreadConfig`** — the typed wrapper around the
  `{"configurable": {"thread_id": ...}}` dict. Used by `replay` and
  `resume`.
- **`replay` / `resume`** — runtime helpers for re-running from a
  checkpoint and continuing after an interrupt.
- **`merge_dict_reducer`, `append_unique_reducer`** — non-trivial
  state-channel reducers users would otherwise mis-write.

See [`../contributing/decisions/0006-five-multi-agent-architectures.md`](../contributing/decisions/0006-five-multi-agent-architectures.md)
for the design contract that locks this in.

## Cross-cutting concerns answered

### Checkpointing

Every factory accepts a checkpointer via `MultiAgentSpec.checkpointer`.
`get_checkpointer("memory" | "sqlite" | "postgres", ...)` is the
canonical entry point; you can also pass any
`langgraph.checkpoint.base.BaseCheckpointSaver` directly.

For multi-tenant or multi-session usage, set
`ThreadConfig.checkpoint_ns` to a tenant or user identifier so
checkpoints isolate cleanly.

### State and reducers

The default state is `ForgeState` (just `messages`). Subclass it to
add channels:

```python
from typing import Annotated
from langgraph_forge import ForgeState, merge_dict_reducer

class MyState(ForgeState):
    artifacts: Annotated[dict, merge_dict_reducer]
```

Pass `state_schema=MyState` in your `MultiAgentSpec` and every node
sees the extended channels.

For trivial reducers (last-write-wins, plain append),
`langgraph.graph.message.add_messages` and Python's `operator.add`
are already in the LangGraph ecosystem; we do not duplicate them.

### Subgraphs

LangGraph natively allows a compiled graph to act as a node. Our
`SpecialistSpec.subgraph` is the typed entry point. Pass a compiled
graph; the multi-agent factory wires it into the parent graph as if
it were a regular ReAct worker.

### Replay

```python
from langgraph_forge import ThreadConfig, replay

result = await replay(
    graph,
    ThreadConfig(thread_id="run-42", checkpoint_id="ckpt-7"),
    # modify=...   # for a counterfactual fork
)
```

### Interrupts

Static interrupts are declarative on the factory:

```python
spec = MultiAgentSpec(
    specialists=[...],
    interrupt_before=("billing_team",),  # pause before delegating to billing
)
```

Dynamic in-node interrupts use LangGraph's own `interrupt()` —
import directly from `langgraph.types`.

To resume:

```python
from langgraph_forge import resume

await resume(graph, ThreadConfig(thread_id="run-42"), human_supplied_value)
```

## What we do not provide

Per [`./initialization-boundary.md`](./initialization-boundary.md)
§ "The package will never do these":

- Per-specialist tool allowlists or output-schema enforcement.
- Retry / timeout / circuit-breaker logic. Compose with LangChain
  fallbacks yourself.
- Cost or token budget caps.
- Trace / observability hooks. The compiled graph supports
  LangChain callbacks; wire them yourself.
- Prompt versioning or content-hash registry.
- Cycle detection or autonomy gates.

If `langgraph-forge` knew about retries or budgets, the boundary
would slip from "compose primitives" to "implement policy". That
is the line ADR-0006 protects.

## See also

- [`../tutorials/`](../tutorials/README.md) — once written, the first
  tutorial will walk through the supervisor pattern end-to-end.
- [`../how-to/`](../how-to/README.md) — recipes for switching
  patterns, adding interrupts, replaying from a checkpoint.
- [`../reference/cli.md`](../reference/cli.md#init) — `--pattern`
  flag reference.
- [`../contributing/decisions/0006-five-multi-agent-architectures.md`](../contributing/decisions/0006-five-multi-agent-architectures.md)
  — the structural decision behind this surface.
