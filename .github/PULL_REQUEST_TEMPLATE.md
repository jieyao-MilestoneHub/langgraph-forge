<!-- Thank you for contributing. Fill in the sections below; delete any that
     are not applicable and note why. -->

## Summary

<!-- What does this change do? One or two sentences. -->

## Why

<!-- Motivating problem, user story, or upstream change driving this PR. -->

## Approach

<!-- High-level description of the implementation path chosen and
     alternatives considered, if any. -->

## Tests

<!-- Describe the tests you added / updated. Per CONTRIBUTING.md, every
     branch needs a test; inputs need typical / edge / invalid cases;
     raise paths need specific exception assertions. -->

- [ ] Logic check (every code branch exercised)
- [ ] Boundary check (typical / edge / invalid inputs)
- [ ] Error handling (each raise has a test asserting the specific exception)
- [ ] Object-state (mutated state verified field-by-field + immutability)

## Checklist

- [ ] Commits follow Conventional Commits (`feat(scope): ...`, `test(scope): ...`, ...)
- [ ] `uv run ruff format --check .` is green
- [ ] `uv run ruff check .` is green
- [ ] `uv run pyright` is green
- [ ] `uv run pytest -q` is green
- [ ] Docs / README updated if public API changed
- [ ] CHANGELOG will be auto-generated from commit messages (no manual edit needed)

## Breaking changes

<!-- If this introduces a breaking change, describe the migration path
     and add a `!` to the relevant commit subjects (feat!: ...). -->
