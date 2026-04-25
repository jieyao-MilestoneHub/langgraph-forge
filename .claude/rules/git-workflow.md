# Git Workflow Rules

## Branch Model — trunk-based

- **`main`** is the only long-lived branch. It is always green on CI.
- **No `develop` branch.** A two-branch model adds ceremony without
  reducing risk for a project this size.
- Releases are **tags** on `main` (`v0.x.ya<n>`, `v0.x.yrc<n>`,
  `v0.x.y`). There is no `release/*` branch.
- Topic branches live in **forks** (for external contributors) or as
  short-lived branches (for maintainers). They are deleted after
  merge.

## Hard Rules

1. **`main` only receives commits via squash-merged PRs**, never direct push
   for non-maintainers. Maintainers may push trivial chores (release version
   bumps) directly only when CI is already green for the change.
2. **External contributors use fork → PR**. They never push to upstream
   `main`. Branch protection enforces this; do not weaken it.
3. **Never force-push to `main`**, even as maintainer. History on `main`
   is permanent.
4. **Never run `gh workflow run` without `--ref main`** — omitting `--ref`
   defaults to whatever branch happens to be set as default; explicit is
   safer.
5. **Never skip hooks** (`--no-verify`, `--no-gpg-sign`) — if a hook fails,
   fix the root cause.
6. **Never push the `v*` tag before everything below is true**:
   - CI on `main` is green for the commit being tagged.
   - PyPI trusted publisher is configured for this repo + workflow + environment.
   - The maintainer is ready to approve the `pypi` environment deployment.

## Fork-and-PR workflow (external contributors)

```bash
# One-time: fork on GitHub, then
git clone https://github.com/<your-username>/langgraph-forge.git
cd langgraph-forge
git remote add upstream https://github.com/jieyao-MilestoneHub/langgraph-forge.git

# For every change
git fetch upstream
git switch main
git merge --ff-only upstream/main          # always fast-forward; never reverse-merge

git switch -c feat/<issue#>-<short-slug>
# ... TDD cycle, commits ...
git push origin feat/<issue#>-<short-slug>

# Open PR via the GitHub UI: source = your fork's branch, target = upstream/main
```

PR titles must follow Conventional Commits because the maintainer
squash-merges and the PR title becomes the commit message.

## Maintainer workflow

```bash
# Topic branch on upstream
git switch main
git pull --ff-only
git switch -c chore/<short-slug>
# ... commits ...
git push -u origin chore/<short-slug>

# PR via gh
gh pr create --base main --head chore/<short-slug>

# Squash-merge after CI green
gh pr merge --squash --delete-branch
```

## TDD Discipline (CRITICAL — applies to every commit adding behaviour)

New behaviour lands as a **test → feat pair**, in that order. No exceptions
for "it's a small change", "I'll add tests later", or "this is just
plumbing". The discipline is the safety net every other rule depends on.

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

### Four check categories (required — see `unit-testing.md`)

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
- **Reverse-merging `main` into a topic branch.** Always fast-forward
  `main` and rebase the topic on top, or merge the topic into `main`.

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

- **≤ 300 LOC diff per commit** excluding generated lock files.
- **One behaviour per test commit, one feature per feat commit** — if you
  type "and" in the subject line, split.

## Issue claiming protocol (for non-maintainers)

1. Comment `I'd like to take this` on the issue.
2. Wait for maintainer to assign — usually within 3 business days.
3. Open a draft PR within **7 days** of assignment (a single failing test
   counts as the start signal).
4. **14 days of no commit activity** on the assigned PR may trigger
   reassignment. Comment to request an extension if needed; almost always
   granted.

Do not open a PR for an issue that hasn't been assigned to you, except for
trivial typo fixes which can skip the assignment step.

## Release flow (maintainer only)

```bash
# Verify CI is green
gh run list --branch main --limit 1

# Bump version + commit
echo '__version__ = "0.x.y"' > src/langgraph_forge/_version.py
git add src/langgraph_forge/_version.py
git commit -m "chore(release): 0.x.y"
git push origin main

# Tag — push triggers publish.yml
git tag -a v0.x.y -m "langgraph-forge 0.x.y"
git push origin v0.x.y
```

The `pypi` environment in GitHub Actions is configured with required
reviewers, so the publish job pauses for explicit human approval before
running `pypa/gh-action-pypi-publish`. This is the second safety belt
in case the tag was pushed accidentally.

## Workflow trigger reference

| Event | Workflow fired | Effect |
|---|---|---|
| Push to `main` | `ci.yml` | matrix lint / type / test |
| PR targeting `main` | `ci.yml` | matrix lint / type / test |
| Push `v*` tag | `publish.yml` | build → (await `pypi` env approval) → PyPI → GH release |

## Related Rules

- `unit-testing.md` — the four check categories referenced above and the
  one-assertion-per-test rule.
- `coding-style.md` — immutability, file organisation, error handling.
- `planning-discipline.md` — when to interrupt the plan to fix a structural
  issue instead of mechanically continuing.
