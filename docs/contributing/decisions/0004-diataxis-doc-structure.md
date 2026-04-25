# ADR-0004: Diátaxis doc structure with audience-folder split

- **Status**: accepted
- **Date**: 2026-04-25
- **Deciders**: @jieyao-MilestoneHub

## Context

With `v0.1.0a1` cut and external contributors expected, the project
needed a documentation home. The default for small projects is "drop
files in `docs/`", which works until the first ambiguity:

- A page describing how the deployment-adapter Protocol is shaped is
  *explanation* for users, *reference* for adapter authors, and
  *implementation tour* for maintainers. Where does it live?
- A "how to contribute" page is for developers, not users; can it
  share `docs/` with the user-facing quickstart, or does it need its
  own home?

Without a framework, those decisions get re-litigated each time a
new doc lands. Three audiences exist even today: package users,
contributors, maintainers.

## Decision

We adopt **[Diátaxis](https://diataxis.fr/)** for the user-facing
quadrants and add an explicit **audience-folder split** at the top
level:

```
docs/
├── tutorials/      # User docs — Learn
├── how-to/         # User docs — Do
├── reference/      # User docs — Look up
├── explanation/    # User docs — Understand
├── contributing/   # Developer docs (assumes cloned repo)
└── governance/     # Maintainer docs (assumes commit access)
```

Each section folder carries a `README.md` explaining what belongs
there. Filenames are kebab-case. Internal links are relative `./...md`
paths so both GitHub and a future static-site renderer resolve them.

ADRs (this directory) live under `contributing/decisions/` with their
own status lifecycle.

## Consequences

**Positive:**

- The "where does this paragraph go?" question has a deterministic
  answer most of the time. The decision tree at
  [`docs/README.md`](../../README.md) catches the rest.
- Audience awareness is enforced at write time: a contributor cannot
  drop architecture notes into `tutorials/` without realising they
  changed audience.
- Diátaxis is well-known and well-documented externally, so
  contributors absorbing the convention have a reference outside our
  own docs.
- Maps cleanly to a future static-site `nav` config; the same source
  layout serves either "one site, multiple sections" or "user site
  + dev site at separate domains" deploy topologies (see ADR-0005).

**Negative:**

- A handful of pages span quadrants legitimately (e.g., a deep
  feature spec is partly reference and partly explanation). The
  convention forces a primary-quadrant pick with cross-links — more
  cognitive load than a flat `docs/` for those edge cases.
- Six folders is more than zero. New contributors must read
  `docs/README.md` to know where their doc goes; this is one extra
  click compared to a flat structure.

**Neutral:**

- We forgo Sphinx's tighter cross-reference / intersphinx model. If
  we ever need it (e.g., to link to LangGraph's API docs by symbol),
  we'd revisit at the deploy round.

## Alternatives considered

- **Flat `docs/` with a `dev/` subdirectory**: rejected. Pre-empts
  the "where does X go?" question only for the user-vs-dev split;
  user-side ambiguity (tutorial vs how-to vs reference) remains.
- **Sphinx with reStructuredText**: rejected for now. More powerful
  but heavier; markdown-native tooling (mkdocs-material) covers our
  needs at our scale.
- **GitHub Wiki**: rejected. Not version-controlled with the code;
  drift between code and docs is the default rather than the
  exception.
- **README-only**: rejected. Survives at v0.1 but does not scale to
  the documentation surface we need by 1.0 (per the
  [`/VERSIONING.md`](../../../VERSIONING.md) § D criteria).

## See also

- [`docs/README.md`](../../README.md) — the index and decision tree.
- [Diátaxis](https://diataxis.fr/) — framework reference.
- ADR-0005 — the related decision to keep docs in this repo and
  defer site deployment.
