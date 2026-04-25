# ADR-0003: No `CHANGELOG.md` in the repo

- **Status**: accepted
- **Date**: 2026-04-25
- **Deciders**: @jieyao-MilestoneHub

## Context

We had wired `cliff.toml` and the `release-notes` job in
`.github/workflows/publish.yml` to generate per-release notes via
`git-cliff --latest --strip header`. Those notes feed
`softprops/action-gh-release` as the GitHub Release body — they
already give consumers a navigable changelog at
`/releases`.

Independently, the maintainer-facing handbook started telling
contributors that "`CHANGELOG.md` is regenerated from commits on
every release tag by `git-cliff`." That was not actually true: the
publish workflow generates `CHANGES.md` (a transient release-notes
file) and uses it for the GH Release body, but it does **not** commit
`CHANGELOG.md` back to the repo.

Two paths were on the table:

1. **Wire publish.yml to commit `CHANGELOG.md` back to `main` after
   a successful publish.**
2. **Drop `CHANGELOG.md` from the repo entirely; let GitHub Releases
   be the canonical changelog.**

Tracking a hand-touchable copy alongside an auto-regenerator is a
classic drift trap: maintainers update one, the other goes stale,
and consumers cannot tell which is canonical.

## Decision

**There is no `CHANGELOG.md` in the repository.** GitHub Releases
(populated by `git-cliff` at tag time) is the canonical changelog.

`pyproject.toml`'s `[project.urls].Changelog` points at
`https://github.com/jieyao-MilestoneHub/langgraph-forge/releases`,
so PyPI and tooling that consume the metadata land on the canonical
view.

Maintainers who want to preview the next release's notes locally
run:

```bash
uv run --with git-cliff git-cliff --unreleased
```

…which prints to stdout without writing a file.

## Consequences

**Positive:**

- One source of truth. No "did I regenerate it before tagging?"
  gotcha at release time.
- One artifact to consume. GitHub Releases is the standard
  open-source surface for this; users browsing the repo expect
  release notes there before a `CHANGELOG.md`.
- The publish workflow does not need write access to push commits
  back to `main`, simplifying the OIDC permission story.

**Negative:**

- Some users expect `CHANGELOG.md` at the repo root (Keep-a-Changelog
  convention). They have to learn that we use `/releases` instead.
  Mitigated by the explicit `Changelog` URL in `pyproject.toml` and
  by a note in `/VERSIONING.md` § H.
- Automated tools that scrape `CHANGELOG.md` will not find one. The
  GitHub Releases API serves the same data; tools that need it can
  use that.

**Neutral:**

- Local previews now require running `git-cliff` rather than reading
  a tracked file. Not a regression for maintainers who already use
  the tool; minor friction for casual contributors.

## Alternatives considered

- **Track `CHANGELOG.md` and have publish.yml commit it back**:
  rejected. Adds workflow complexity and OIDC permissions, and
  introduces the drift trap on every manual edit.
- **Track `CHANGELOG.md` and forbid manual edits via pre-commit**:
  rejected. The drift hole moves from "manual edits diverge" to
  "regeneration job can be skipped"; net no improvement.
- **Towncrier-style fragment files**: rejected. Useful when many
  contributors land changes simultaneously and need to write
  changelog entries inline; over-engineered for current scale.

## See also

- `cliff.toml` — section parser config that drives release-note
  generation.
- `.github/workflows/publish.yml` § `release-notes` — the job that
  invokes git-cliff at tag time.
- [`/VERSIONING.md`](../../../VERSIONING.md) § H — canonical
  source-of-truth map.
