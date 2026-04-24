"""LLM provider factory backed by ``init_chat_model``."""

from __future__ import annotations

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from langgraph_forge.core.specs import ModelSpec


def get_model(spec: ModelSpec) -> BaseChatModel:
    """Instantiate a chat model for the given :class:`ModelSpec`.

    The call is routed through LangChain's ``init_chat_model`` so every
    provider it supports (OpenAI, Anthropic, xAI/Grok, Google,
    Bedrock Converse, Azure, Groq, Ollama, ...) is reachable without
    this wrapper knowing about them.

    Provider-specific kwargs -- ``max_tokens``, ``top_p``, ``base_url``,
    Bedrock ``region_name`` -- belong in :attr:`ModelSpec.extra` and are
    spread into the call.
    """
    return init_chat_model(
        model=spec.model,
        model_provider=spec.provider,
        temperature=spec.temperature,
        **spec.extra,
    )
