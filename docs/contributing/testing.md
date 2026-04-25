# Testing guide

How tests are organised, what's mocked where, and what you must do
before opening a PR.

## Running the suite

```bash
# Unit tests (default; fast, no network, no real LLM)
uv run pytest -q

# Specific path
uv run pytest tests/unit/builders -q

# Single test by name
uv run pytest tests/unit/core/test_specs_specialist.py::TestSpecialistSpecNamePattern::test_valid_names_accepted -q

# Integration tests (opt-in; will not run by default)
uv run pytest -m integration

# Everything (unit + integration)
uv run pytest
```

All four quality gates that CI runs:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q
```

Pre-commit runs the first three on every commit; CI runs all four
on every push and PR across the matrix
`{ubuntu, macos, windows} × {3.11, 3.12, 3.13}`.

## Layout — mirrors `src/`

```
tests/
├── unit/
│   ├── core/
│   │   ├── test_specs_model.py
│   │   ├── test_specs_specialist.py
│   │   ├── test_specs_mcp.py
│   │   ├── test_state.py
│   │   └── test_errors.py
│   ├── builders/
│   │   ├── test_llm.py
│   │   ├── test_single.py
│   │   ├── test_supervisor.py
│   │   ├── test_mcp.py
│   │   └── test_checkpoint.py
│   ├── deploy/
│   │   ├── test_base.py
│   │   ├── test_registry.py
│   │   ├── test_direct.py
│   │   └── test_cloud_stubs.py
│   └── scaffold/
│       ├── test_render.py
│       └── test_cli.py
└── integration/
    └── test_init_and_run.py
```

Each test file targets one source file. Test classes group by
behaviour; test methods are one assertion each.

## TDD discipline

Every public behaviour lands as a `test(scope): …` commit (red) →
`feat(scope): …` commit (green) pair. The full discipline lives in
[`.claude/rules/git-workflow.md`](../../.claude/rules/git-workflow.md).
The short version:

1. Write the failing test. Run it. Confirm it fails for the
   documented reason.
2. Write the minimum production code that turns it green.
3. (Optional) refactor with no behaviour change.

Combine red + green into one `feat` commit only when the test +
impl together are < ~30 LOC and separating them adds no review value.

## Four check categories

Every public behaviour needs tests across each applicable category.
Spell out "not applicable" in the PR description with a reason.

| Category | What to assert | Example |
|---|---|---|
| **Logic** | Every code branch is exercised. | Each `if/elif/else` arm has a test that takes that arm. |
| **Boundary** | Each parameter has typical / edge / invalid cases. | `name="x" * 64` (max-length valid), `name="x" * 65` (over-length invalid), `name="1bad"` (bad pattern). |
| **Error handling** | Every `raise` path is covered with the specific exception class and message asserted. | `with pytest.raises(ValidationError, match="name"): ...` — never `assert not raises`. |
| **Object state** | Mutations to persistent state verify both fields that changed AND fields that did not change. | `assert spec.name == "researcher" and spec.tools == []` (cancel that — one assertion per test; use a structural compare). |

## One assertion per test

Multi-field checks use **structure comparison**, not multiple lines of
`assert`:

```python
# Good — one assertion via structural compare
def test_dispatch_args(self) -> None:
    with patch("...init_chat_model") as mock:
        get_model(ModelSpec(model="gpt-4o", provider="openai"))

    mock.assert_called_once_with(
        model="gpt-4o",
        model_provider="openai",
        temperature=0.2,
    )

# Bad — three assertions, the second hides if the first fails
def test_dispatch_args(self) -> None:
    with patch("...init_chat_model") as mock:
        get_model(ModelSpec(model="gpt-4o", provider="openai"))

    assert mock.called
    assert mock.call_args.kwargs["model"] == "gpt-4o"
    assert mock.call_args.kwargs["model_provider"] == "openai"
```

## Mock discipline

**Mock the boundary, not the dependency.**

We import `init_chat_model` at `langgraph_forge.builders.llm`. Patch
that module-local symbol, not `langchain.chat_models.init_chat_model`:

```python
# Good
with patch("langgraph_forge.builders.llm.init_chat_model") as mock:
    ...

# Wrong — patches a different binding; our code still calls the real one
with patch("langchain.chat_models.init_chat_model") as mock:
    ...
```

Boundaries that get mocked in unit tests:

| Symbol | Where it's used | Mocked at |
|---|---|---|
| `init_chat_model` | `builders/llm.py` | `langgraph_forge.builders.llm.init_chat_model` |
| `MultiServerMCPClient` | `builders/mcp.py` | `langgraph_forge.builders.mcp.MultiServerMCPClient` |
| `SqliteSaver` / `PostgresSaver` | `builders/checkpoint.py` | `langgraph.checkpoint.{sqlite,postgres}.{Sqlite,Postgres}Saver` (lazy import; patch at the source module) |
| Cloud SDKs (`boto3`, `google.cloud.aiplatform`, `azure.ai.agents`) | `deploy/{bedrock,vertex,azure}.py` | Not exercised in unit tests — the stubs raise `NotImplementedError` before any SDK import. |
| `importlib.metadata.entry_points` | `deploy/registry.py` | `langgraph_forge.deploy.registry.entry_points` |

Things we do NOT mock in unit tests:

- `create_react_agent`, `create_supervisor`, `MemorySaver` — they are
  upstream dependencies, not external boundaries. Our tests call the
  real implementations and rely on them to behave correctly. If
  upstream breaks, integration tests catch it.

## Async tests

`pytest-asyncio` is configured with `asyncio_mode = "auto"` in
`pyproject.toml`, so `async def test_…` works without a marker:

```python
@pytest.mark.parametrize(...)
async def test_load_mcp_tools_returns_get_tools_result(self, ...) -> None:
    ...
```

Use `AsyncMock` for awaited methods:

```python
client = MagicMock()
client.get_tools = AsyncMock(return_value=[])
```

## Determinism

- **No network**. CI is offline-capable.
- **No real LLM API**. Mock at the `init_chat_model` boundary.
- **No wall-clock**. Use `freezegun` if a test depends on the current
  time (none do today).
- **No unseeded randomness**. We don't seed because no test currently
  uses random; if one does, seed it explicitly.

## Integration tests

Lives under `tests/integration/`. Gated by `@pytest.mark.integration`
or by simply being in that directory (the `markers` config in
`pyproject.toml` registers the marker).

Run them with:

```bash
uv run pytest -m integration
```

The integration suite is **not** part of the default `pytest` run, so
CI ships it separately when configured. Today's only integration test
exercises the full CLI scaffold path against the real templates and
real `MultiServerMCPClient` on a temp directory; no network involved.

## See also

- [`.claude/rules/unit-testing.md`](../../.claude/rules/unit-testing.md)
  — the four-category framework in detail.
- [`.claude/rules/git-workflow.md`](../../.claude/rules/git-workflow.md)
  — TDD discipline and commit shape.
- [`repository-tour.md`](./repository-tour.md) — what each module
  contains, so you know where new tests go.
