# Contributing — developer documentation

**Audience**: anyone touching the source code, in-tree or in a fork.
Assumes the reader has cloned the repo and run `uv sync --dev`.

**Where to start**: the root [`/CONTRIBUTING.md`](../../CONTRIBUTING.md)
covers the contribution flow (fork → branch → PR → review). This
directory holds the deeper material that doesn't fit on the entry
page.

## Pages in this section

- [`repository-tour.md`](./repository-tour.md) — what each subpackage
  contains, in one page.
- [`testing.md`](./testing.md) — TDD discipline, what's mocked at the
  boundary, how CI runs the suite.
- `adding-a-provider.md` — walkthrough for a new LLM provider
  template (lands when the first community provider PR shows up).
- `adding-an-adapter.md` — in-tree and out-of-tree paths for new
  deployment adapters (lands with the first community adapter PR).
- [`decisions/`](./decisions/README.md) — Architecture Decision
  Records (ADRs).

## Conventions

The full conventions live at the parent [`docs/README.md`](../README.md);
specific notes for contributor docs:

- Assume the reader has access to the repo. Use full file paths
  (`src/langgraph_forge/...`) and reference real symbols.
- Cross-link generously: contributors don't read documents end to
  end, they jump.
- An ADR is **not** a contributor doc — it's a permanent record of a
  decision. If your page describes "the way we do X today", it
  belongs here. If it describes "the decision we made on day Y to
  do X instead of Z", it goes in
  [`decisions/`](./decisions/README.md).

## See also

- Repository-level rules: [`.claude/rules/`](../../.claude/rules/) —
  TDD, unit testing, coding style, planning discipline.
- Maintainer-only material: [`../governance/`](../governance/README.md).
