"""Finance-document agent — drop into your existing Python project.

Import :func:`build_finance_agent` from your code, or run this file
directly to smoke-test against ``$ANTHROPIC_API_KEY``.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from langgraph_forge import (
    AdapterConfig,
    DirectAdapter,
    ModelSpec,
    create_single_agent,
    get_model,
)


@tool
def parse_invoice(text: str) -> dict[str, Any]:
    """Extract vendor, amount, and line items from raw invoice text."""
    # Replace with regex / OCR / vendor library — this stub keeps the
    # example self-contained and offline.
    return {
        "vendor": "Acme Corp",
        "amount": 1250.50,
        "line_items": [
            {"desc": "License", "price": 1000.00},
            {"desc": "Support", "price": 250.50},
        ],
    }


CENT_TOLERANCE = 0.01


@tool
def validate_invoice(parsed: dict[str, Any]) -> bool:
    """Return True iff line_items sum to the stated amount (within 1¢)."""
    total = sum(item["price"] for item in parsed["line_items"])
    return abs(total - parsed["amount"]) < CENT_TOLERANCE


SYSTEM_PROMPT = (
    "You are a finance assistant. Use parse_invoice on user-provided "
    "invoice text, then validate_invoice on the result. Reject invoices "
    "that fail validation."
)


def build_finance_agent():
    """Compile the ReAct agent with the two finance tools."""
    model = get_model(ModelSpec(provider="anthropic", model="claude-sonnet-4-6"))
    return create_single_agent(
        model=model,
        tools=[parse_invoice, validate_invoice],
        prompt=SYSTEM_PROMPT,
    )


if __name__ == "__main__":
    import asyncio

    agent = build_finance_agent()
    adapter = DirectAdapter()
    deployed = adapter.prepare(agent, AdapterConfig(project_name="finance"))
    result = asyncio.run(
        adapter.invoke(
            deployed,
            {"messages": [{"role": "user", "content": "Parse this invoice: Acme Corp $1250.50"}]},
        )
    )
    print(result["messages"][-1].content)
