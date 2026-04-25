# How-to guides

**Audience**: people who already know `langgraph-forge` basics and need
to **accomplish a specific goal**.

**What goes here**: task recipes. Each one answers a concrete "How do
I…" question with the shortest path to "done". The reader is in a
hurry and knows what they want.

**What does NOT go here**: introductions (those go in
[`../tutorials/`](../tutorials/README.md)), exhaustive flag
documentation ([`../reference/`](../reference/README.md)), or
conceptual background ([`../explanation/`](../explanation/README.md)).

## How-to guides in this section

(None yet. Likely first additions, when surface stabilises:)

- *Switch deployment target without rewriting your graph*
- *Add a custom LLM provider via the CLI scaffolder*
- *Wire an MCP server into a supervisor agent*
- *Extend `ForgeState` with a custom channel*

For **multi-MCP-server scenarios beyond what `load_mcp_tools`
covers** (registry-style discovery, lifecycle management, cross-server
dependency wiring, hot reload), see
[`mcp-forge-core`](https://pypi.org/project/mcp-forge-core/) on PyPI.
The boundary between this package and `mcp-forge-core` is documented
at [`../explanation/initialization-boundary.md`](../explanation/initialization-boundary.md)
§ "Multi-MCP-server scenarios — where to outgrow this".

## Authoring guidelines

- **Title is a goal**: start with "How to…" or a verb phrase
  (*"Switch deployment target"*, not *"Deployment swap"*).
- **One goal per guide**: if the recipe branches into "if you have X,
  do Y; if Z, do W", split into multiple guides.
- **Skip the "why"**: explanation belongs in
  [`../explanation/`](../explanation/README.md). Link to it from the
  how-to if a reader genuinely needs context, but keep the recipe
  itself focused.
- **Real, runnable code**: every step is a command or a code block
  that the reader copies. Don't paraphrase.

## See also

- [Diátaxis: How-to guides](https://diataxis.fr/how-to-guides/).
