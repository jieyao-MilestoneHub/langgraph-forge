# langgraph-forge

> Initialise LangGraph-based agent architectures: pick a provider, a pattern, a deployment — get a runnable project.

[![PyPI - Version](https://img.shields.io/pypi/v/langgraph-forge.svg)](https://pypi.org/project/langgraph-forge/)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/langgraph-forge.svg)](https://pypi.org/project/langgraph-forge/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/CoreNovus/langgraph-forge/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/CoreNovus/langgraph-forge/actions/workflows/ci.yml)

## Why?

LangGraph's primitives — `init_chat_model`, `create_react_agent`, `langgraph-supervisor`, `langchain-mcp-adapters`, cloud-runtime wrappers — are individually excellent but scattered across five packages with inconsistent config shapes. Every team building an agent re-writes the same wiring.

`langgraph-forge` absorbs that wiring into thin, opinionated factories plus a CLI scaffolder. **We compose, we don't reimplement.** The value is a coherent surface and a trade-off-aware starter, not new primitives.

## Install

```bash
pip install langgraph-forge
# or, for optional cloud adapters:
pip install 'langgraph-forge[bedrock,vertex,azure]'
```

## Quickstart (under a minute)

```bash
# 1. Scaffold a project
langgraph-forge init my-agent --provider anthropic --pattern supervisor --deploy direct --no-input
cd my-agent

# 2. Install + set credentials
cp .env.example .env        # then edit
uv sync --extra dev

# 3. Smoke-test the generated graph (uses mocked LLM)
uv run pytest tests/unit -q

# 4. Run it
uv run python -m my_agent
```

## Matrix

| Provider (`--provider`) | Pattern (`--pattern`) | Deployment (`--deploy`) |
|---|---|---|
| `anthropic`, `openai`, `grok`, `google`, `bedrock`, `azure` | `single`, `supervisor` | `direct`, `bedrock`, `vertex`, `azure` |

All combinations scaffold end-to-end. `direct` is fully functional in v0.1; cloud adapters (`bedrock` / `vertex` / `azure`) ship as Protocol-conformant contract stubs — the scaffolded `deploy.py` imports successfully and the smoke test passes, but calling the cloud `prepare` / `invoke` raises `NotImplementedError` until the SDK glue lands in v0.2.

## Library usage (without the CLI)

```python
from langgraph_forge import (
    ModelSpec,
    SpecialistSpec,
    create_supervisor_agent,
    get_model,
)

supervisor = get_model(ModelSpec(model="claude-opus-4-7", provider="anthropic"))
worker_model = ModelSpec(model="claude-haiku-4-5", provider="anthropic")

graph = create_supervisor_agent(
    supervisor_model=supervisor,
    specialists=[
        SpecialistSpec(
            name="researcher",
            prompt="You gather facts.",
            model=worker_model,
        ),
        SpecialistSpec(
            name="summariser",
            prompt="You produce concise summaries.",
            model=worker_model,
        ),
    ],
    supervisor_prompt="Delegate research and summarisation to specialists.",
)
```

Swap providers by changing `provider="anthropic"` to `"openai"`, `"xai"`, `"google_genai"`, `"bedrock_converse"`, or `"azure_openai"`. Swap deployment by replacing `DirectAdapter` with `BedrockAgentCoreAdapter` / `VertexAgentEngineAdapter` / `AzureAIAgentAdapter`.

## MCP integration

```python
from langgraph_forge import MCPConfig, MCPServerConfig, load_mcp_tools

config = MCPConfig(
    servers={
        "filesystem": MCPServerConfig(
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        ),
    }
)
tools = await load_mcp_tools(config)
```

## Extending: writing a new deployment adapter

Every adapter satisfies the `DeploymentAdapter` Protocol (name, extras, prepare, invoke, template fragment). Third-party packages register via the `langgraph_forge.deployment_adapters` entry-point group, which means **adding a fifth target does not require a PR to this repo.**

```toml
# your_package/pyproject.toml
[project.entry-points."langgraph_forge.deployment_adapters"]
modal = "your_package.modal_adapter:ModalAdapter"
```

After `pip install your-package`, `langgraph-forge list-deploy` includes `modal` and `--deploy modal` works in `init`.

## Not included — by design

Listed so expectations stay calibrated. These are out of scope in v0.1, many permanently:

- Swarm pattern / non-supervisor multi-agent topologies (may return in v0.3+)
- LangSmith / OpenTelemetry / tracing / metrics
- Prompt versioning, PromptPack, content_hash, prompt registry, eval harness
- Tool allowlists, SideEffectGate, autonomy gates, budget / cost ceilings, cycle detection
- Schema registry, output-envelope validation, per-specialist `output_type`
- Peer review, human review queue, ExceptionTicket, routing hints
- HTTP / REST serving, WebSocket, SSE, web UI
- Auth(n/z), permissions, multi-tenancy, rate limiting
- DynamoDB / S3 / custom persistence beyond `langgraph.checkpoint.*`
- Model-chain fallback (compose LangChain's `with_fallbacks` yourself)
- Streaming helpers (`graph.astream()` is already the answer)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for private disclosure.

## License

MIT — see [LICENSE](LICENSE).
