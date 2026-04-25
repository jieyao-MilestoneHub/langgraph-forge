# Governance — maintainer documentation

**Audience**: maintainers (currently `@jieyao-MilestoneHub`). Assumes
commit access to the upstream repository and admin rights on the
GitHub repo + the PyPI project.

**Where to start**: the root [`/MAINTAINERS.md`](../../MAINTAINERS.md)
is the operational handbook (release process, repo settings, branch
protection, PyPI trusted publisher). This directory holds the deeper
playbooks that don't fit on the entry page.

## Pages in this section

- [`triage-playbook.md`](./triage-playbook.md) — how to triage
  incoming issues, when to apply each label, when to close.

## Conventions

- **Operational, not conceptual**: explanation belongs in
  [`../explanation/`](../explanation/README.md), even when the
  audience is the maintainer. This directory documents *how* you do
  things on the repo, not *why* the repo is structured the way it is.
- **Defensive against single-maintainer drift**: write every page so
  a future co-maintainer can step in without a 1-on-1 walkthrough.

## Versioning policy

The release cadence and compatibility promise live in
[`/VERSIONING.md`](../../VERSIONING.md). Maintainers reference it from
the release process; consumers reference it from the README. A single
source of truth.
