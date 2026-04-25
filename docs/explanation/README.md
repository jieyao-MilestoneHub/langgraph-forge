# Explanation

**Audience**: people who want to **understand** the project — the
concepts, the design choices, the trade-offs.

**What goes here**: discussion-style writing that answers "why does
it work this way?". The reader has time and is curious.

**What does NOT go here**: step-by-step paths
([`../tutorials/`](../tutorials/README.md) /
[`../how-to/`](../how-to/README.md)), or lookup material
([`../reference/`](../reference/README.md)).

## Pages in this section

- [`initialization-boundary.md`](./initialization-boundary.md) — what
  the package does, what's the user's job, and what's permanently
  out of scope. The structural charter; read before adding a new
  public symbol.

(Future additions:)

- *Architecture overview* — what each subpackage does and why.
- *Why supervisor first, swarm later* — the multi-agent pattern
  trade-off.
- *Why `init_chat_model` over per-provider classes* — the LLM
  abstraction choice.

## Authoring guidelines

- **Discussion form**: complete sentences, paragraphs, maybe
  diagrams. Bullet lists are for reference, not explanation.
- **Honest about trade-offs**: every choice has costs. Name them.
  Pretending the chosen path is universally best erodes trust.
- **Link to ADRs** (`../contributing/decisions/`) for the
  high-stakes structural decisions; explanation pages summarise,
  ADRs preserve.
- **Standalone**: a reader can land here from a search engine and
  still understand the page without prior context.

## See also

- [Diátaxis: Explanation](https://diataxis.fr/explanation/).
