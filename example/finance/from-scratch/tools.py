"""Finance tools — copy this file to ``src/finance_mvp/tools.py``.

Authored after running::

    langgraph-forge init finance_mvp \\
      --provider anthropic --pattern single \\
      --deploy direct --checkpointer memory

Then apply ``graph.patch`` to register these tools in the scaffolded
``src/finance_mvp/graph.py``.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


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
