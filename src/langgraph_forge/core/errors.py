"""Public exception types for langgraph-forge."""

from __future__ import annotations


class ForgeError(Exception):
    """Base class for all langgraph-forge public exceptions.

    Catching this class catches every error the library raises on the
    happy-path boundary (config validation, missing extras, registry
    lookup failures).
    """


class ForgeConfigError(ForgeError):
    """Raised when a user-supplied config is rejected.

    Wraps Pydantic ValidationError at the boundary (e.g., MCPConfig loaded
    from JSON) so downstream callers only need to catch ForgeError.
    """


class MissingExtraError(ForgeError):
    """Raised when an optional extra is required but not installed.

    The message always contains the exact ``pip install langgraph-forge[...]``
    command so the remediation path is discoverable from the traceback
    alone.
    """

    def __init__(self, extra: str, feature: str) -> None:
        self.extra = extra
        self.feature = feature
        super().__init__(
            f"The optional extra `{extra}` is required to use {feature}. "
            f"Install it with: pip install langgraph-forge[{extra}]"
        )
