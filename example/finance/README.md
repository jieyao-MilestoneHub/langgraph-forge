# Finance-document agent in ~30 lines

You have invoices. You want an agent that extracts vendor + amount and
rejects ones that don't add up. Here's the smallest path with
`langgraph-forge`.

## What you get

A ReAct agent backed by Claude Sonnet 4.6 with two Python tools you
own:

- `parse_invoice(text) -> dict` — extracts vendor, amount, line items
- `validate_invoice(parsed) -> bool` — fails if line items don't sum
  to the stated total

The package wires the agent loop, tool dispatch, state, and the
in-memory checkpointer. You write the finance rules. See
[the boundary](../../docs/explanation/initialization-boundary.md) for
why this split matters.

## Pick a path

### A. You already have a Python project

`pip install langgraph-forge`, then drop in
[`integrate-into-existing/finance_agent.py`](integrate-into-existing/finance_agent.py)
and call `build_finance_agent()` from your code. One file, ~35 lines.
Run it directly to smoke-test:

```bash
export ANTHROPIC_API_KEY=...
python example/finance/integrate-into-existing/finance_agent.py
```

### B. You're starting fresh

```bash
pip install langgraph-forge
langgraph-forge init finance_mvp \
  --provider anthropic --pattern single \
  --deploy direct --checkpointer memory
cd finance_mvp
```

Then add two finance-specific things on top of the scaffold:

1. Copy [`from-scratch/tools.py`](from-scratch/tools.py) to
   `src/finance_mvp/tools.py`.
2. Apply [`from-scratch/graph.patch`](from-scratch/graph.patch) to
   register the tools in the generated graph:

   ```bash
   git apply ../example/finance/from-scratch/graph.patch
   ```

Run it:

```bash
pip install -e .
export ANTHROPIC_API_KEY=...
python -m finance_mvp.main
```

We commit only the user-added layer (tools + patch), not the
scaffold output. The scaffold is what `langgraph-forge init` already
generates; duplicating it here would drift against the templates.

## Out of scope

Real PDF parsing (the parser returns a hand-crafted dict, marked
`# replace with regex / OCR / vendor library`), persistence beyond
in-memory, auth, multi-tenancy, eval. The package is intentionally
narrow — see the repo README's
[Not included](../../README.md#not-included--by-design) section.
