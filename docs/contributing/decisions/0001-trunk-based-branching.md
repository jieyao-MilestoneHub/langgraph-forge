# ADR-0001: Trunk-based branching with `main` only

- **Status**: accepted
- **Date**: 2026-04-25
- **Deciders**: @jieyao-MilestoneHub

## Context

The project initially used a `develop` + `main` two-branch model
(develop active, main release-only via PR). With a single maintainer
and a fork-based external-contributor flow, that model added ceremony
without reducing risk:

- Every release required a `develop → main` PR with no diff beyond
  the version bump.
- Contributors had to reason about which branch their PR targets,
  inviting "wrong-base" mistakes.
- CI had to enumerate both branches in its push trigger.
- Tag-based releases on either branch are equivalent under
  trunk-based; the second branch added no isolation that tags don't
  already provide.

## Decision

We use **trunk-based branching with `main` as the only long-lived
branch.** Releases are tags on `main` (`v0.1.0a1`, `v0.1.0`, …).
There is no `develop` branch and no `release/*` branch.

External contributors fork the repo, branch from `main` in their
fork, and open PRs against upstream `main`. Maintainers create
short-lived feature branches on upstream and merge them via squash.
Direct push to `main` is reserved for trivial chores (release
version bumps) and is governed by branch protection.

## Consequences

**Positive:**

- One mental model. Contributors don't need to know about develop.
- One CI trigger to maintain.
- Release flow is "tag and push"; no extra PR needed at release time.
- `main` always reflects the latest accepted state, simplifying
  triage of "is this in the latest release?" questions.

**Negative:**

- A bad squash-merge into `main` is more visible than into `develop`.
  Mitigated by branch protection (required reviews, required CI
  green) and CODEOWNERS on release-critical files.
- We give up the implicit "stable vs in-development" signal that two
  branches provide. Mitigated by the pre-1.0 versioning rules in
  [`/VERSIONING.md`](../../../VERSIONING.md): every minor bump may
  be breaking, so users opt into a specific tag rather than tracking
  a branch.

**Neutral:**

- Hot-fix patches now branch from a tag rather than from a stable
  branch. The mechanics are equivalent: `git switch -c hotfix/X
  v0.1.0`, fix, tag `v0.1.1`. No `release/0.1.x` branch is
  maintained unless and until we need to support multiple stable
  lines simultaneously (post-1.0 problem).

## Alternatives considered

- **Keep `develop` + `main`**: rejected. The cost (release-time PR,
  contributor mental model) outweighed the benefit (a "stable line"
  signal that pre-1.0 versioning already provides).
- **Three branches** (e.g., `main` / `staging` / `develop`):
  rejected. Strictly more ceremony; useful for deployment pipelines
  that promote artifacts across environments, which a Python library
  does not have.
- **GitFlow proper**: rejected. Designed for products with multiple
  in-flight feature branches and scheduled release windows, not for
  a single-maintainer library on a continuous release cadence.

## See also

- [`.claude/rules/git-workflow.md`](../../../.claude/rules/git-workflow.md)
  — operational rules implementing this decision.
- [`/MAINTAINERS.md`](../../../MAINTAINERS.md) § Branch model.
- [`/CONTRIBUTING.md`](../../../CONTRIBUTING.md) — fork-and-PR flow.
