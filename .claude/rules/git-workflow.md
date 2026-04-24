# Git Workflow Rules

## Branch Strategy (CRITICAL)

- **`develop`** — active development branch; all work happens here
- **`main`** — release branch; NEVER push or deploy directly

## Hard Rules

1. **All commits go to `develop`**, never directly to `main`
2. **`develop` → `main` ONLY via Pull Request** — no direct merges, no force pushes
3. **Never run `gh workflow run` without `--ref develop`** — omitting `--ref` defaults to `main`
4. **Never trigger deploys targeting `main`** unless explicitly asked by the user after a PR merge
5. **`main` merges only at release cuts** (`0.x.ya`, `0.x.yrc1`, `0.x.y`) — routine feature work stays on `develop`
6. **Never skip hooks** (`--no-verify`, `--no-gpg-sign`) — if a hook fails, fix the root cause
7. **Never push the `v*` tag before the maintainer is ready to release** — pushing triggers the OIDC publish workflow against PyPI

## TDD Discipline (CRITICAL — applies to every commit adding behaviour)

New behaviour lands as a **test → feat pair**, in that order. No exceptions
for "it's a small change", "I'll add tests later", or "this is just
plumbing". The discipline is the safety net we rely on throughout every
other rule.

### The red → green → refactor cycle

1. **Red** — write a failing test that asserts **one specific behaviour**.
   Run it, confirm it fails **for the documented reason** (not for a typo
   or unrelated import error). Commit:
   ```
   test(<scope>): <behaviour statement>
   ```
   Describe in the commit body why the test fails right now ("module does
   not exist yet", "function returns wrong value", etc.).

2. **Green** — write the **minimum production code** that turns the test
   green. Do not extend scope beyond the assertion. Commit:
   ```
   feat(<scope>): <behaviour statement>
   ```
   Same behaviour statement as the red commit, different prefix.

3. **Refactor** (optional) — only after green. No new tests, no behaviour
   diff, no test deletions that change coverage. Commit:
   ```
   refactor(<scope>): <what + why>
   ```

### Pair combination rule

Red + green may collapse into **one** `feat(<scope>): ...` commit **only when
all** of the following hold:

- Test file + impl file together under ~30 LOC diff
- Reviewing them separately adds no review value (i.e., the test is so
  obvious that seeing it red before green does not inform the reviewer)
- The test is NOT the first test in a new module (first-test-in-module
  always gets its own red commit because it also sets up the test
  infrastructure)

When in doubt, split.

### Four check categories (required — see `.claude/rules/unit-testing.md`)

Each public behaviour must have tests across **every applicable** category:

| Category | What to assert |
|---|---|
| **Logic** | Every code branch (if / elif / else, match, early return) executes with a matching test |
| **Boundary** | Each parameter has typical / edge / invalid cases (e.g., empty list, single element, max size, off-by-one, None, Unicode) |
| **Error handling** | Every `raise` path has a test asserting the specific exception class and message match; no `assert not raises` as a proxy |
| **Object state** | Mutations of persistent state verify both the fields that changed AND the fields that did NOT change |

"Not applicable" is a valid answer but must be justified in the PR
description (e.g., "no state mutation in this pure function → object-state
check skipped").

### Commit-level quality gates

Every commit must keep these green (pre-commit enforces locally; CI enforces
on push):

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv run pytest -q`

"I'll fix lint in the next commit" commits are forbidden. Broken CI is a
broken build; broken builds block every other contributor.

### Anti-patterns (will be rejected in review)

- **Code first, tests later** (even within the same PR). Commit order tells
  reviewers whether TDD was actually followed.
- **Green commit with unrelated scope** — the feat commit must only contain
  the impl the preceding test commit demanded.
- **Mega test commits** with 10+ assertions spanning unrelated behaviours.
  Split by behaviour.
- **Tests that assert on implementation details** (private methods, mock
  call order when order is not the contract). Tests should fail only when
  a contract breaks.
- **Mocks that return hand-crafted payloads instead of recorded fixtures**
  for external SDK shapes. Drift there bites silently.
- **`pytest.mark.skip` as a way to land red tests** — if the test cannot
  be made green right now, don't land the test yet.

## Commit Message Convention (Conventional Commits)

Format: `<type>(<scope>): <subject>`.

| Type | Use for |
|---|---|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `docs` | Docs-only change |
| `test` | Tests added or refactored (red phase of TDD) |
| `refactor` | Structural change, no behaviour diff |
| `perf` | Performance improvement |
| `build` | Build system / dependency change |
| `ci` | GitHub Actions / pre-commit change |
| `chore` | Repo metadata, release cuts, misc |
| `style` | Formatting only |
| `revert` | Revert a prior commit |

Scope is the subpackage when applicable: `feat(builders)`, `test(deploy)`,
`refactor(scaffold)`. Breaking changes use `!`: `feat(deploy)!: rename
prepare to build`. The `commit-msg` pre-commit hook
(`conventional-pre-commit`) rejects non-conforming messages.

## Commit Size

- **≤ 300 LOC diff per commit** excluding generated lock files
- **One behaviour per test commit, one feature per feat commit** — if you
  type "and" in the subject line, split

## Correct Commands

```bash
# Work on develop
git switch develop
git pull

# Short-lived feature branch
git switch -c feat/my-thing

# After the red/green cycle, push the branch
git push -u origin feat/my-thing

# Open PR targeting develop (NOT main)
gh pr create --base develop --head feat/my-thing

# Trigger CI on develop (always specify --ref)
gh workflow run ci.yml --ref develop

# Release cut: PR develop → main, then tag on main after merge
gh pr create --base main --head develop --title "Release 0.1.0a1"
# After the PR merges:
git switch main && git pull
git tag -a v0.1.0a1 -m "langgraph-forge 0.1.0a1"
git push origin v0.1.0a1   # triggers publish.yml (OIDC → PyPI)
```

## Environment Mapping

| Branch / Tag | Workflow fired | Target |
|---|---|---|
| push to `develop` | `ci.yml` | matrix lint / type / test |
| PR to `develop` | `ci.yml` | matrix lint / type / test |
| push `v*` tag | `publish.yml` | PyPI (via OIDC trusted publishing) |

## Related Rules

- `.claude/rules/unit-testing.md` — the four check categories referenced in
  the TDD section and the one-assertion-per-test rule
- `.claude/rules/coding-style.md` — immutability, file organisation, error
  handling
- `.claude/rules/planning-discipline.md` — when to interrupt the plan to
  fix a structural issue instead of mechanically continuing
