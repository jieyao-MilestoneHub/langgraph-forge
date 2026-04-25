# Reference

**Audience**: people who already know what they want to do and need
to **look up an exact value** — a CLI flag, an API symbol, an
environment variable, an extras name.

**What goes here**: fact tables and exhaustive enumerations. Reference
material is consulted, not read end-to-end.

**What does NOT go here**: walkthroughs (those go in
[`../tutorials/`](../tutorials/README.md)), recipes
([`../how-to/`](../how-to/README.md)), or rationale
([`../explanation/`](../explanation/README.md)).

## Pages in this section

- [`cli.md`](./cli.md) — every `langgraph-forge` subcommand and its
  flags.
- `api/` — auto-generated API reference (lands with mkdocstrings in
  the deploy round).

## Authoring guidelines

- **Complete**: list every flag, every parameter, every supported
  value. Partial reference is worse than no reference because it
  misleads.
- **Stable structure**: every entry follows the same shape (name,
  type, default, description, example). Readers scan; consistency
  speeds scanning.
- **Cross-link, don't restate**: when reference material refers to a
  concept, link to the explanation page rather than re-explaining.

## See also

- [Diátaxis: Reference](https://diataxis.fr/reference/).
