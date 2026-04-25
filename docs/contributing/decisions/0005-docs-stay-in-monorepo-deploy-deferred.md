# ADR-0005: Docs stay in this repo; deploy deferred

- **Status**: accepted
- **Date**: 2026-04-25
- **Deciders**: @jieyao-MilestoneHub

## Context

Two questions came up alongside ADR-0004:

1. Should documentation live in **this repository** or be split into
   a separate `langgraph-forge-docs` repo?
2. Should we **deploy** a documentation site now, or just shape the
   source for an eventual deploy?

The maintainer signalled that developer docs will eventually be
hosted under a public domain, but did not want to commit to a deploy
in the same round as the docs structure itself.

## Decision

**Documentation lives in this repository, under `docs/`.** No split
to a separate docs repo, now or in the foreseeable future.

**No site deployment in this round.** No `mkdocs.yml`, no theme, no
Pages / Cloudflare Pages / Vercel CI step, no DNS. The `docs/`
structure is laid out so that a future deploy round is a
configuration-only change.

Concretely, the forward-compatibility commitments are:

- Folder hierarchy maps 1:1 to URL paths
  (`docs/how-to/foo.md` → `/how-to/foo/`).
- kebab-case filenames double as URL slugs.
- Internal links use relative `./...md` paths that both GitHub and
  mkdocs-material resolve.
- Each section folder has a `README.md` that becomes the section
  landing page when rendered (mkdocs convention with
  `use_directory_urls=True`).
- Assets (when added) live under `docs/assets/<area>/...` and are
  referenced by relative path.
- No front matter on individual pages; H1 = title is sufficient
  until a renderer reads the metadata.

Either deploy topology — "one site with sections" or "user site +
developer site at separate domains" — is satisfied by the same
source layout. The choice is made at deploy round, not now.

## Consequences

**Positive:**

- Docs version with code: a PR can update both implementation and
  docs atomically; no second-repo sync workflow.
- One `git log`, one set of CI checks, one CODEOWNERS file. Lower
  cognitive load.
- Forward-compatible: when we deploy, the work is config + theme,
  not content migration.
- Single-repo discoverability: contributors finding the package on
  GitHub also find the docs without leaving the repo.

**Negative:**

- Any large docs-only PR appears in the same activity stream as code
  PRs. Mitigated by `docs(...)` Conventional Commit prefixes.
- We do not benefit from a separate docs site's UX (search,
  versioned docs, social cards) until the deploy round. Reading on
  GitHub is fine for the current scale (≤ 10 substantive pages).

**Neutral:**

- Versioned docs (e.g., `/v0.1/`, `/v0.2/`) are not implemented now.
  Whether to support them is a deploy-round question; the source
  layout doesn't preclude it.

## Alternatives considered

- **Separate `langgraph-forge-docs` repository**: rejected. Sync
  cost (every code PR may need a paired docs PR) is high relative
  to the benefit (none, at our scale; not even isolation, since the
  docs cover the same code).
- **GitHub Wiki**: rejected for the same reasons as ADR-0004 plus
  this one — wikis are not versioned with the code.
- **Deploy now under a temporary subdomain** (e.g.,
  `langgraph-forge.github.io`): rejected. Maintainer wants a
  specific public domain. Setting up an interim site that is then
  thrown away is busywork.
- **Markdown only forever, never deploy**: rejected. Maintainer
  intent is to deploy eventually; designing for "never deploy" would
  forfeit the cheap forward-compat we get by spending no extra
  effort now.

## See also

- ADR-0004 — the Diátaxis structure that sits in this repo.
- [`docs/README.md`](../../README.md) § "Forward-compatibility with
  site deployment" — the operational checklist enforcing this ADR.
