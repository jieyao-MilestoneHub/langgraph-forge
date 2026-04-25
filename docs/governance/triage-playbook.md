# Triage playbook

How to handle incoming issues, in order of action. Audience:
maintainers (currently `@jieyao-MilestoneHub`).

## Daily / weekly cadence

Aim to look at the issue queue **at least weekly**. Issues that sit
without a maintainer touching them for 7+ days erode reporter trust;
even a `triage` label + "thanks, will look this week" comment keeps
the relationship healthy.

## Order of operations on a fresh issue

1. **Read the report** in full. If reproduction steps are missing or
   ambiguous, label `needs-repro` and ask one specific question. Do
   not start triaging until the answer arrives.
2. **Classify the issue type**. Replace `triage` (or the lack of
   any classification label) with one of:
   - `bug` — broken behaviour or spec violation.
   - `enhancement` — new capability or improvement to existing.
   - `documentation` — docs gap, error, or improvement.
   - `provider` — request for a new LLM provider option.
   - `adapter` — request for a new deployment adapter.
   - `security` — vulnerability; **stop and route through
     SECURITY.md** instead of public triage.
   - `dependencies` — upstream library bump or vulnerability.
   - `ci` — workflow / pre-commit / release pipeline.
3. **Apply meta-labels** as appropriate:
   - `good first issue` — a newcomer can solve in <2 hours
     without deep codebase knowledge.
   - `help wanted` — you want external help (does not imply low
     difficulty).
   - `blocked` — depends on an upstream change or external
     decision; add a comment naming the blocker.
   - `question` — user question rather than a bug or feature
     request; consider migrating to GitHub Discussions.
   - `discussion` — open-ended thread that doesn't have a
     concrete deliverable; same migration consideration.
4. **Decide the disposition**:
   - In scope, you'll handle it → leave unassigned, the reporter
     can claim or watch the queue.
   - In scope, want help → add `help wanted` and (if newbie-safe)
     `good first issue`.
   - **Out of scope** per README's "Not included — by design" list
     → close with `wontfix`, leave a comment explaining which line
     of the anti-scope list applies.
   - **Duplicate** → close with `duplicate`, link the canonical
     issue.
   - **Cannot reproduce after follow-up** → close with `wontfix`
     and a note inviting reopen with a fresh repro.

## Assigning a claimed issue

When a contributor comments "I'd like to take this":

1. Confirm the issue is **classified** (no longer `triage`).
2. Confirm the contributor is not currently assigned to two or more
   open issues. (Single-maintainer projects can flex this; just be
   aware of attention budget.)
3. Click **Assignees** → add their handle. Comment "Assigned, looking
   forward to your draft PR within ~7 days. Ping me if you need
   guidance on the approach."
4. If no draft PR appears within 14 days and there's been no
   conversation, comment "Hey, are you still planning to work on
   this? Happy to extend if so; otherwise I'll unassign so others
   can pick it up." Wait 7 more days, then unassign if silent.

The 7/14/21-day timeline is a guideline, not a contract. Adjust for
holidays, contributor history, and complexity. Communicate the
adjustment.

## Closing an issue

- **Always** comment before closing. `wontfix` and `duplicate` need a
  reason; `done` issues can use the auto-close from a PR's
  `Closes #N`.
- Lock the issue **only** if abusive comments arrive. Locking a
  closed-but-civil issue is a hostile signal.

## Security reports

If an issue body or title looks like it might be a security
vulnerability:

1. **Do not respond in the public thread**. Public commenting
   discloses the issue.
2. Hide the offending content (Mark as off-topic / sensitive) if
   the disclosure is severe.
3. Comment briefly: "This looks like a security issue — please
   re-report via our private vulnerability reporting channel
   (see SECURITY.md). I'm closing this issue to limit public
   exposure."
4. Close the issue.
5. Follow up in the private channel.

See [`/SECURITY.md`](../../SECURITY.md) for the canonical
disclosure process.

## Labels source of truth

The label set lives in [`.github/labels.yml`](../../.github/labels.yml).
If you need a label that does not exist, edit that file first, run
the `gh label create` step from
[`/MAINTAINERS.md`](../../MAINTAINERS.md), then apply it. Don't
create labels in the GitHub UI without updating the YAML — it
creates drift between the canonical file and the repo.

## See also

- [`/MAINTAINERS.md`](../../MAINTAINERS.md) — operational handbook;
  this playbook is its expanded triage section.
- [`/CONTRIBUTING.md`](../../CONTRIBUTING.md) § "Claiming an issue"
  — the contributor side of the assignment protocol.
- [`/SECURITY.md`](../../SECURITY.md) — private disclosure flow.
