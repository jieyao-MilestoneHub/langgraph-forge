# Contributing to langgraph-forge

Thanks for taking time to help. This is a small, opinionated project; the
contribution process is correspondingly opinionated. Read this whole doc
before opening your first PR — it pays back in shorter review cycles.

> **Looking for deeper material?** [`docs/contributing/`](./docs/contributing/README.md)
> has the repository tour, testing guide, and Architecture Decision
> Records. This page is the entry point; that directory is the rest.

## TL;DR — the path from idea to merged PR

1. Find an existing issue or open a new one with the right template.
2. If you want to work on it, comment "I'd like to take this".
3. Wait for the maintainer to assign you (usually within ~3 business days).
4. **Fork** the repo and clone your fork.
5. Branch from `main`, make changes with **TDD discipline**, push to your fork.
6. Open a PR from your fork against the upstream `main` and fill in the template.
7. Address review feedback. Maintainer squash-merges when CI is green and review is approved.

There is no `develop` branch and no direct push for non-maintainers. `main`
is trunk; releases are tags on `main`.

## Filing issues

Use the templates in `.github/ISSUE_TEMPLATE/`:

- **bug.yml** — something broke that worked, or a clear spec violation.
- **feature.yml** — new capability or improvement. Check `README.md`'s
  "Not included — by design" list first; out-of-scope proposals will be closed.
- **provider_request.yml** — new LLM provider option for the CLI.
- **adapter_request.yml** — new deployment target. Note that out-of-tree
  adapters (separate PyPI packages) need no upstream change; file here
  only if you want the adapter shipped in this repo.

Search existing issues before filing a duplicate. Issues without a clear
reproduction or scope statement may be closed pending more detail.

## Claiming an issue

Maintainer assignment is the contract that you'll deliver. The protocol:

1. Comment `I'd like to take this` (or similar) on the issue.
2. Wait for the maintainer to add you under **Assignees**. Don't fork until
   you're assigned — it avoids two contributors duplicating work.
3. Open a **draft** PR within **7 days** of assignment. The draft can be
   skeletal (one failing test, an empty function); it's the signal that
   work has started.
4. If the draft PR sees no commit activity for **14 days**, the maintainer
   may unassign and re-open the issue for someone else. Comment if you
   need an extension — that's almost always granted.

Look for `good first issue` and `help wanted` labels if you're new to the
codebase.

## Setup

```bash
# Fork on GitHub, then:
git clone https://github.com/<your-username>/langgraph-forge.git
cd langgraph-forge
git remote add upstream https://github.com/jieyao-MilestoneHub/langgraph-forge.git

# Install uv (one-time; pick one)
# Windows (PowerShell):  irm https://astral.sh/uv/install.ps1 | iex
# macOS / Linux:         curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and pre-commit hooks
uv sync --dev
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

## Branching and committing

```bash
# Sync with upstream
git fetch upstream
git switch main
git merge --ff-only upstream/main

# Branch from main (in your fork)
git switch -c feat/123-add-together-provider
```

Branch naming: `<type>/<issue-number>-<short-slug>`. Common types: `feat`,
`fix`, `docs`, `refactor`, `test`, `ci`. Drop the issue number for tiny
issue-less work.

**TDD is the only way new behaviour lands.** See
`.claude/rules/git-workflow.md` for the full rules; the short version:

1. `test(scope): <behaviour>` — failing test (red).
2. `feat(scope): <behaviour>` — minimum impl (green).
3. `refactor(scope): ...` — optional, no behaviour diff.

Commits use **Conventional Commits** (`feat`, `fix`, `docs`, `test`,
`refactor`, `perf`, `build`, `ci`, `chore`, `style`, `revert`). The
`commit-msg` pre-commit hook rejects non-conforming messages.

## Submitting the PR

1. Push your branch to your fork: `git push origin feat/123-add-together-provider`.
2. On GitHub, click **Compare & pull request**. Target is upstream
   `main`. Source is your fork's branch.
3. Fill in `.github/PULL_REQUEST_TEMPLATE.md`. Include `Closes #123` so the
   issue auto-closes on merge.
4. Mark the PR as **Draft** while still iterating; **Ready for review**
   once you want maintainer eyes on it.
5. CI will run on your fork against the matrix
   (`{ubuntu, macos, windows} × {3.11, 3.12, 3.13}`). All checks must be
   green before review.

### Review expectations

- Maintainer responds within **7 business days** of "Ready for review".
- Reviews focus on:
  - TDD discipline (commit shape, test/feat pairing).
  - Four check categories from
    [`.claude/rules/unit-testing.md`](./.claude/rules/unit-testing.md):
    logic, boundary, error handling, object-state.
  - Public API surface (anything exported from `langgraph_forge.__init__`).
  - Scope: did the PR stay within what its issue asked for?
- Address review by **adding new commits**, not by rewriting history. The
  maintainer squashes at merge time, so your commits don't need to be
  pristine — they need to be reviewable.

### Merge

The maintainer **squash-merges** all PRs. The squashed commit message
follows the PR title (Conventional Commits). Your individual commits live
in the PR's history but don't pollute `main`.

## Licensing

By submitting a PR you agree your contribution is licensed under the MIT
license (the project license). No CLA, no DCO sign-off.

## What's out of scope

The README has a permanent "Not included — by design" list. PRs touching
these areas (HTTP API, auth, prompt registry, streaming helpers, etc.)
will be closed without review unless the issue was explicitly approved
beforehand.

## Reporting security issues

See [SECURITY.md](SECURITY.md). **Do not file public issues for security bugs.**

## See also

- [`MAINTAINERS.md`](MAINTAINERS.md) — release process and repo
  governance (relevant if you eventually become a maintainer).
- [`.claude/rules/git-workflow.md`](./.claude/rules/git-workflow.md) — the
  full TDD + Conventional Commits + branch rules.
- [`.claude/rules/unit-testing.md`](./.claude/rules/unit-testing.md) — the
  four check categories, one-assertion rule, mock discipline.
