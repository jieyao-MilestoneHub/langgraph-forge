# Architecture Decision Records (ADRs)

This directory holds the project's Architecture Decision Records — a
permanent log of the structural choices we have made, why we made them,
and what we considered instead.

## Why ADRs

Documentation in
[`../../tutorials/`](../../tutorials/README.md),
[`../../how-to/`](../../how-to/README.md),
[`../../reference/`](../../reference/README.md), and
[`../../explanation/`](../../explanation/README.md) tells readers
**how the project is today**.

ADRs answer a different question: **why is the project the way it is,
and what was on the table when we decided?** That question matters
when:

- A new contributor proposes reverting a decision because they don't
  see the original tension.
- A future maintainer needs to know whether a constraint is still
  load-bearing or has gone stale.
- An evaluation surfaces whether the decision still makes sense as
  the project scales.

A flat changelog or git history lets someone find *when* a decision
landed; ADRs let someone find *why* in one focused document.

## Status lifecycle

| Status | Meaning |
|---|---|
| `proposed` | Drafted; under discussion. Open for comment. |
| `accepted` | The decision is in force. **The body of the ADR is now read-only.** Errors get an erratum at the bottom; substantive changes mean superseding. |
| `superseded by ADR-NNNN` | A later ADR has replaced this one. The replaced ADR stays in the directory; its `Status:` line points at the replacement. |
| `rejected` | The proposal was considered and dropped. Kept on file so the same proposal does not re-appear without learning from why it was rejected last time. |

## File naming

`NNNN-short-slug.md` where `NNNN` is a four-digit zero-padded
sequence. Slug is kebab-case, descriptive, and stable — once an ADR
is `accepted`, the filename does not change.

```
0001-trunk-based-branching.md
0002-deployment-adapter-protocol-shape.md
...
```

ADR numbers are allocated by the next-highest-unused integer.
Conflicts on parallel PRs are resolved by the second PR rebasing onto
a fresh number.

## Index

| # | Title | Status |
|---|---|---|
| [0000](./0000-template.md) | Template | n/a |
| [0001](./0001-trunk-based-branching.md) | Trunk-based branching with `main` only | accepted |
| [0002](./0002-deployment-adapter-protocol-shape.md) | DeploymentAdapter Protocol shape | accepted |
| [0003](./0003-no-changelog-md-in-repo.md) | No `CHANGELOG.md` in the repo | accepted |
| [0004](./0004-diataxis-doc-structure.md) | Diátaxis doc structure with audience-folder split | accepted |
| [0005](./0005-docs-stay-in-monorepo-deploy-deferred.md) | Docs stay in this repo; deploy deferred | accepted |

## How to propose a new ADR

1. Copy [`0000-template.md`](./0000-template.md) to
   `NNNN-your-slug.md` with the next free number.
2. Fill in the four sections; mark **Status: proposed** at the top.
3. Open a PR. Discuss in PR review. Tighten the wording.
4. When the maintainer approves, change **Status** to `accepted` and
   merge. The ADR is then read-only; future changes require a
   superseding ADR.

## How to supersede an existing ADR

1. Author a new ADR (`NNNN-replacement.md`) explaining the change
   and why the old reasoning no longer holds.
2. In the same PR, edit only the **Status** line of the old ADR to
   `Status: superseded by ADR-NNNN`. Do not edit the body.
3. The replaced ADR stays in this directory permanently as a record
   of the path we did not take.

## CODEOWNERS

`/docs/contributing/decisions/` requires explicit maintainer approval
on changes (see `.github/CODEOWNERS`). This is the structural defence
against accidental edits to accepted decisions.
