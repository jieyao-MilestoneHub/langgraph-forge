# How to compose router + supervisor + verifier into a baseline flow

You have five named multi-agent patterns: `supervisor`, `swarm`,
`hierarchical`, `router`, `custom`. The "general baseline" shape that
many production agents land on — *classify the request, delegate to a
team, verify the output before returning* — is **not** a sixth pattern.
It is a composition recipe: stack the patterns you already have via
`SpecialistSpec.subgraph`. This guide shows the recipe end-to-end.

## The shape

```
classifier → supervisor team → deterministic verifier → END
   (router)    (per-domain)         (subgraph)
```

The `router` decides which domain handles the request (`billing`,
`tech_support`, `sales`). Each domain is a `supervisor`-pattern team
with its own specialist workers. The team's compiled graph is wrapped
as `SpecialistSpec(subgraph=...)`. After the team runs, a
deterministic verifier (a one-node `StateGraph`) checks the output
before the graph returns.

## Step 1 — Build a deterministic verifier subgraph

The verifier is plain Python wrapped in a `StateGraph`. It can flag
unsupported claims, fail closed if no answer was produced, or attach
metadata for downstream logging — whatever your domain requires.

```python
from langgraph.graph import END, START, StateGraph

from langgraph_forge import ForgeState


def verify(state: dict) -> dict:
    last = state["messages"][-1] if state["messages"] else None
    if last is None or not getattr(last, "content", "").strip():
        # Encoded code: domain rule says "never return an empty answer".
        raise ValueError("verifier: empty response is not acceptable")
    return {}


def make_verifier() -> "CompiledStateGraph":
    builder = StateGraph(ForgeState)
    builder.add_node("verify", verify)
    builder.add_edge(START, "verify")
    builder.add_edge("verify", END)
    return builder.compile()
```

## Step 2 — Build per-domain supervisor teams

Each team is its own `create_supervisor_agent` graph. The team
supervisor decides which of its specialists answers each turn.

```python
from langgraph_forge import (
    MultiAgentSpec,
    SpecialistSpec,
    create_supervisor_agent,
    get_model,
)
from my_app.providers import specialist_model_spec, supervisor_model_spec

billing_specialists = [
    SpecialistSpec(
        name="invoice_lookup",
        prompt="Look up invoice details by ID.",
        model=specialist_model_spec(),
    ),
    SpecialistSpec(
        name="refund_processor",
        prompt="Issue refunds within policy limits.",
        model=specialist_model_spec(),
    ),
]

billing_team = create_supervisor_agent(
    MultiAgentSpec(specialists=billing_specialists),
    supervisor_model=get_model(supervisor_model_spec()),
    supervisor_prompt="You manage the billing team.",
)
```

Repeat for `tech_support_team`, `sales_team`, etc.

## Step 3 — Wrap each team + the verifier in a route target

`RouteSpec.target` accepts any `SpecialistSpec`. The subgraph mode
slots a compiled graph into the route directly — no LLM construction
inside the router itself.

```python
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from langgraph_forge import ForgeState, RouteSpec, SpecialistSpec


def team_with_verifier(name: str, team: CompiledStateGraph) -> SpecialistSpec:
    """Compose a domain team with a deterministic verifier post-step."""
    builder = StateGraph(ForgeState)
    builder.add_node("team", team)
    builder.add_node("verifier", make_verifier())  # from Step 1
    builder.add_edge(START, "team")
    builder.add_edge("team", "verifier")
    builder.add_edge("verifier", END)
    composed = builder.compile()
    return SpecialistSpec(name=name, subgraph=composed)


ROUTES = [
    RouteSpec(
        name="billing",
        description="Billing, invoices, refunds.",
        target=team_with_verifier("billing", billing_team),
    ),
    RouteSpec(
        name="tech_support",
        description="Bugs, error messages, login issues.",
        target=team_with_verifier("tech_support", tech_support_team),
    ),
]
```

## Step 4 — Compile the router on top

The router classifies the inbound request and dispatches to the
matching route. Because every route's target is already a composed
`team → verifier` subgraph, you get the full baseline flow from one
top-level compile.

```python
from langgraph_forge import RouterSpec, create_router_agent

CLASSIFIER_PROMPT = (
    "You are a router. Decide which route best handles the user's "
    "request. Output only the route name."
)

graph = create_router_agent(
    RouterSpec(routes=ROUTES),
    classifier=supervisor_model_spec(),
    classifier_prompt=CLASSIFIER_PROMPT,
)
```

That's the whole baseline. Five public symbols, three encoding
choices (LLM specialists, LLM supervisors, encoded verifier), and
one compile call.

## Why this is a composition recipe, not a pattern

Per ADR-0006, the package ships *topologies* — concrete graph shapes
with named edges. `Router → Team → Verifier` is one of an unbounded
number of shapes you can build from the five primitives by reusing
`SpecialistSpec.subgraph`. Promoting every common stack to a "named
pattern" would balloon the public surface without earning its place
under the boundary's "we ship" column.

If your composition repeats across projects, factor it into a helper
in your own codebase. The factories stay primitive on purpose.

## See also

- [Multi-agent architectures](../explanation/multi-agent-architectures.md)
  — the five patterns and when each one applies.
- [Initialisation boundary](../explanation/initialization-boundary.md)
  — why composition is documentation rather than a sixth factory.
- [ADR-0006](../contributing/decisions/0006-five-multi-agent-architectures.md)
  — the architectural decision behind this split.
