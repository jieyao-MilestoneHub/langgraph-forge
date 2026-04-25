# How to resume an interrupted graph

When a graph pauses at an `interrupt(...)` call (or a static
`interrupt_before` / `interrupt_after` boundary), the runtime is
sitting on a checkpoint waiting for a human or external system to
supply the resume value. Resuming is a one-line LangGraph idiom.

## The recipe

```python
from langgraph.types import Command

from langgraph_forge import ThreadConfig

# `graph` is whatever your factory returned (compiled graph).
# `thread` is the same ThreadConfig you used to invoke originally.
thread = ThreadConfig(thread_id="run-42")

# Approve / supply the resume value:
result = await graph.ainvoke(
    Command(resume="approved"),
    thread.to_langgraph(),
)
```

The `value` you pass to `Command(resume=...)` flows into the
`interrupt(...)` call site that paused the graph. Its shape is
**your contract** with the code that emitted the interrupt — a
boolean for approval gates, a string for content overrides, a dict
for structured inputs.

## Why we removed the `resume` helper

`langgraph-forge` 0.2.0a1 shipped a `resume(graph, thread, value)`
helper. In 0.3.0a1 we removed it: the function body was a single
line — `await graph.ainvoke(Command(resume=value),
thread.to_langgraph())` — and hiding one upstream import (`from
langgraph.types import Command`) does not earn its place on the
public API.

`replay` stays because its `modify` branch encodes the
counterfactual-fork semantic, which is non-trivial. `resume` was
pure 1-line sugar; the trade-off heuristic
(see [boundary doc § Why some wrappers are so thin](../explanation/initialization-boundary.md))
deletes it.

## See also

- [Initialisation boundary § "Why some wrappers are so thin"](../explanation/initialization-boundary.md)
  — the criteria we use to decide what stays public.
- LangGraph upstream `interrupt()` and `Command` documentation
  for the full semantics of resume values.
