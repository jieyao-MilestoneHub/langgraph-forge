"""Adapter discovery via Python entry points.

The ``langgraph_forge.deployment_adapters`` group is the plugin
boundary: first-party adapters (direct / bedrock / vertex / azure) are
declared in :file:`pyproject.toml`, and third-party packages
(``langgraph-forge-modal``, etc.) register their own adapters the
same way. The core library never learns about individual plugins by
name.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

ENTRY_POINT_GROUP = "langgraph_forge.deployment_adapters"

_REQUIRED_ATTRS = ("name", "requires_extras", "prepare", "invoke", "template_fragment")


def _looks_like_adapter(cls: Any) -> bool:
    """Structural check against the DeploymentAdapter shape.

    We avoid ``isinstance(instance, DeploymentAdapter)`` here because
    that would require instantiating every discovered class, and
    constructors may have side effects (e.g. reading AWS credentials).
    """
    return all(hasattr(cls, attr) for attr in _REQUIRED_ATTRS)


def discover_adapters() -> dict[str, type]:
    """Return every registered adapter class keyed by entry-point name.

    Malformed entries (loaded class missing required attributes) are
    silently filtered so a broken third-party plugin degrades to "not
    available" rather than breaking the whole registry.
    """
    discovered: dict[str, type] = {}
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        loaded = ep.load()
        if _looks_like_adapter(loaded):
            discovered[ep.name] = loaded
    return discovered


def get_adapter(name: str) -> type:
    """Look up a single adapter class by name.

    Raises :class:`KeyError` with the requested name quoted if no
    adapter is registered under that name; callers (typically the CLI)
    translate this into a user-facing ``langgraph-forge doctor`` hint.
    """
    adapters = discover_adapters()
    if name not in adapters:
        raise KeyError(f"unknown deployment adapter: {name!r}")
    return adapters[name]
