# langgraph-forge documentation

Welcome. This directory holds everything that doesn't belong at the
repository root, organised by **audience** and (for user docs) by
**purpose** following the [Diátaxis](https://diataxis.fr/) framework.

## Where to start

**You want to use the package** (`pip install langgraph-forge`):

| You want to… | Go to… |
|---|---|
| Learn the project step by step | [`tutorials/`](./tutorials/README.md) |
| Get a specific task done | [`how-to/`](./how-to/README.md) |
| Look up a CLI flag, an API symbol, an env var | [`reference/`](./reference/README.md) |
| Understand why something is the way it is | [`explanation/`](./explanation/README.md) |

**You want to contribute to or maintain the repo:**

| You are… | Go to… |
|---|---|
| A first-time contributor (setup, workflow, tests) | [`contributing/`](./contributing/README.md) |
| A maintainer (releases, repo settings, triage) | [`governance/`](./governance/README.md) |

## Decision tree for "where does my new doc go?"

```
Is this for someone running `pip install langgraph-forge`?
├─ Yes → user-facing
│   ├─ Walks through learning a feature step-by-step? → tutorials/
│   ├─ Recipe to accomplish a specific task? → how-to/
│   ├─ Lookup table / API surface? → reference/
│   └─ "Why does it work this way?" → explanation/
│
└─ No → repo-facing
    ├─ How to contribute, write tests, build features? → contributing/
    ├─ Decision worth preserving for future contributors? → contributing/decisions/  (ADR)
    └─ How to operate the repo (release, triage, secrets)? → governance/
```

If your question is "all of the above" — write multiple short docs, one
per quadrant, and cross-link.

## Conventions

- **Filename**: kebab-case, `.md` extension. Filename doubles as the
  URL slug for the future site.
- **Internal links**: relative paths ending in `.md`
  (`[link](./other-doc.md)`). Renders on GitHub today; works under
  mkdocs-material when we deploy.
- **Section landing page**: every folder has a `README.md` explaining
  what lives there.
- **Audience encoded by location**, not by filename suffix. Don't
  call a file `dev-architecture.md` — put it under `contributing/`
  instead.
- **Assets** (images, diagrams): `docs/assets/<area>/...`, referenced
  with relative paths.

## What's deliberately not here

- A rendered website. The structure is forward-compatible with
  mkdocs-material; deploying is a separate plan that lands when
  there's a domain to point at and ≥ 10 substantive pages to publish.
- Auto-generated API reference. Same reason: gates on the rendering
  toolchain.
- Front matter on individual pages. Required only by static-site
  generators; we'll add it when we adopt one.

See [`contributing/decisions/0004-diataxis-doc-structure.md`](./contributing/decisions/0004-diataxis-doc-structure.md)
and [`contributing/decisions/0005-docs-stay-in-monorepo-deploy-deferred.md`](./contributing/decisions/0005-docs-stay-in-monorepo-deploy-deferred.md)
for the rationale.
