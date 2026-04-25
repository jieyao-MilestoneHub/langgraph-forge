# Maintainers Guide

Operational handbook for repo maintainers. Currently the only maintainer
is the repo owner (`@jieyao-MilestoneHub`); this doc captures everything
that's not in `CONTRIBUTING.md` so a future co-maintainer can be onboarded
by reading one file.

## Branch model

**Trunk-based with one long-lived branch: `main`.**

- All work merges into `main` via PRs from forks (external) or feature
  branches (maintainer).
- `main` is always green: every commit on it has passed CI on the matrix
  `{ubuntu, macos, windows} × {3.11, 3.12, 3.13}`.
- Releases are **tags** on `main`. There is no `release/*` branch.

There is no `develop` branch. The `develop → main` two-branch model adds
ceremony without reducing risk for a small project.

## Required GitHub repo settings (one-time)

The CLI calls in `### Apply via gh` below codify what's automatable. Items
under `### Apply via UI` need maintainer hands.

### Apply via `gh`

```bash
# Description, homepage, topics
gh repo edit jieyao-MilestoneHub/langgraph-forge \
  --description "Initialise LangGraph-based agent architectures: pick a provider, a pattern, a deployment — get a runnable project." \
  --homepage "https://pypi.org/project/langgraph-forge/" \
  --add-topic langgraph,langchain,agents,multi-agent,supervisor,mcp,llm,scaffold,pypi

# Default branch (after main exists on the remote)
gh repo edit jieyao-MilestoneHub/langgraph-forge --default-branch main

# Merge options: squash only (matches our changelog story)
gh repo edit jieyao-MilestoneHub/langgraph-forge \
  --enable-merge-commit=false \
  --enable-squash-merge=true \
  --enable-rebase-merge=false \
  --delete-branch-on-merge=true

# Issues / Discussions
gh repo edit jieyao-MilestoneHub/langgraph-forge --enable-issues=true
gh api repos/jieyao-MilestoneHub/langgraph-forge -X PATCH -f has_discussions=true

# Labels (one-shot; sourced from .github/labels.yml)
# See .github/labels.yml for the full list.
```

### Apply via UI (gh cannot configure these reliably)

1. **Branch protection on `main`** — `Settings → Branches → Add branch protection rule`:
   - Branch name pattern: `main`
   - Require a pull request before merging: **on**
     - Require approvals: **1**
     - Dismiss stale approvals when new commits are pushed: **on**
   - Require status checks to pass before merging: **on**
     - Require branches to be up to date: **on**
     - Required status checks: `lint-type-test (ubuntu-latest, 3.12)` (add the rest you care about; CI matrix names are the job-name + matrix combo).
   - Require linear history: **on** (matches squash-merge convention).
   - Do not allow bypassing the above settings: **on**.
   - Restrict deletions: **on**.
   - Disallow force pushes: **on**.
2. **Tag protection** — `Settings → Tags → New rule`:
   - Pattern: `v*`. Only maintainers can create / delete.
3. **Environment `pypi`** — `Settings → Environments → New environment`:
   - Name: `pypi`.
   - Required reviewers: yourself (so a tag push pauses for explicit
     human approval before publishing).
   - No deployment branch policy (tags are not branches).
4. **PyPI trusted publisher** — at <https://pypi.org/manage/account/publishing/>:
   - PyPI project name: `langgraph-forge`
   - Owner: `jieyao-MilestoneHub`
   - Repository: `langgraph-forge`
   - Workflow filename: `publish.yml`
   - Environment name: `pypi`

### Verifying

```bash
# Default branch is main
gh repo view jieyao-MilestoneHub/langgraph-forge --json defaultBranchRef -q '.defaultBranchRef.name'

# Squash-only merge config
gh repo view jieyao-MilestoneHub/langgraph-forge --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed
```

## Triage workflow

When a new issue arrives:

1. Apply `triage` if you can't classify within 5 minutes.
2. Replace `triage` with one or more of: `bug`, `enhancement`, `provider`,
   `adapter`, `documentation`, `ci`, `dependencies`, `security`,
   `wontfix`, `duplicate`.
3. Add `good first issue` for issues a newcomer can solve in <2 hours
   without knowing the codebase.
4. Add `help wanted` for issues you want external help on.
5. Assign to a contributor when they ask for it (see CONTRIBUTING.md
   issue-claiming protocol).
6. Close `wontfix` and `duplicate` with a brief explanation; never
   leave a closed issue without a reason.

## PR review checklist

Before approving any PR, verify:

- [ ] CI is green across the matrix (no skipped jobs).
- [ ] Conventional Commit titles. The PR title becomes the squashed
      commit message, so it must conform.
- [ ] Test commit precedes feat commit (TDD evidence).
- [ ] Four check categories covered or "not applicable" justified.
- [ ] Public API additions are also re-exported from
      `src/langgraph_forge/__init__.py` if they belong on the stable surface.
- [ ] No new dependencies on cloud SDKs in core (lazy-import in adapter
      only).
- [ ] README / CONTRIBUTING / docs updated if behaviour changed.

## Release process

Pre-release tags: `v0.x.ya<n>` (alpha), `v0.x.yrc<n>` (release candidate).
Stable: `v0.x.y`. Until 1.0, breaking changes can land in a minor bump.

```bash
# 1. Confirm main is green
gh run list --branch main --limit 1

# 2. Bump version
echo '__version__ = "0.x.y"' > src/langgraph_forge/_version.py
git add src/langgraph_forge/_version.py
git commit -m "chore(release): 0.x.y"
git push origin main

# 3. Tag
git tag -a v0.x.y -m "langgraph-forge 0.x.y"
git push origin v0.x.y
```

The `v*` tag push triggers `.github/workflows/publish.yml`:

1. **build** job — `uv build` produces wheel + sdist; `twine check --strict`
   validates metadata; artefacts uploaded.
2. **publish** job — pauses at the `pypi` environment for your explicit
   approval (configured in `### Apply via UI` step 3), then
   `pypa/gh-action-pypi-publish` uses OIDC to publish.
3. **release-notes** job — `git-cliff` generates per-tag notes; a GitHub
   release is created with `prerelease: true` if the tag contains
   `a` / `b` / `rc`.

After publish:

- Verify the package on PyPI: <https://pypi.org/project/langgraph-forge/>.
- Verify the GitHub release: <https://github.com/jieyao-MilestoneHub/langgraph-forge/releases>.
- Smoke-test in a clean venv: `pip install langgraph-forge==0.x.y && langgraph-forge version`.

## Changelog

`CHANGELOG.md` is regenerated from commits on every release tag by
`git-cliff` (see `cliff.toml`). Don't hand-edit the file; the publish
workflow overwrites it. Hand-curated content goes in the GitHub Release
description, which `git-cliff` also generates.

If you need to regenerate the changelog locally for review:

```bash
uv run --with git-cliff git-cliff -o CHANGELOG.md
```

## Yanking a bad release

If a published version turns out to be broken:

1. Yank on PyPI: <https://pypi.org/manage/project/langgraph-forge/releases/>
   → click the broken version → **Yank**. This hides it from `pip install`
   resolution but leaves it downloadable for users who already pinned it.
2. Don't delete the GitHub release; mark it as `prerelease` if appropriate
   and add a note explaining the yank.
3. Cut a fix release: bump version, fix, follow the normal release flow.

Never delete a published version on PyPI — `pip` caches and downstream
users may have pinned it. Yank is the right tool.
