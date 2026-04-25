"""Lock the public API surface.

Any addition or removal in :mod:`langgraph_forge.__init__.__all__` is a
diff against this file, which forces a review checkpoint. Reviewers
apply the boundary check from
``docs/explanation/initialization-boundary.md`` before accepting the
diff.

If you arrived here because this test failed: either you intended to
change the public surface (update the EXPECTED_PUBLIC_API set, write
the corresponding entry in the next release notes via Conventional
Commits, and ensure the change clears the boundary check) or you
exported a symbol unintentionally (revert it).
"""

from __future__ import annotations

import langgraph_forge

EXPECTED_PUBLIC_API: frozenset[str] = frozenset(
    {
        # Exception hierarchy
        "ForgeError",
        "ForgeConfigError",
        "MissingExtraError",
        # Value-object specs
        "ModelSpec",
        "SpecialistSpec",
        "MCPConfig",
        "MCPServerConfig",
        "MultiAgentSpec",  # Phase 1 — topology-agnostic multi-agent config
        "ThreadConfig",  # Phase 1 — typed wrapper for LangGraph configurable dict
        # Default state schema
        "ForgeState",
        # Reducers — Phase 1 (non-trivial state-channel merge functions)
        "merge_dict_reducer",
        "append_unique_reducer",
        # Builder factories
        "get_model",
        "create_single_agent",
        "create_supervisor_agent",
        "load_mcp_tools",
        "get_checkpointer",
        # Runtime helpers — Phase 1
        "replay",
        "resume",
        # Deployment surface
        "DeploymentAdapter",
        "DirectAdapter",
        "AdapterConfig",
        # Re-exports (justified in initialization-boundary.md)
        "BaseTool",
        "Command",
        # Version metadata
        "__version__",
    }
)


class TestPublicAPISurface:
    def test_all_attribute_matches_locked_set(self) -> None:
        # __all__ is the canonical declaration; we compare as sets so
        # alphabetical ordering is not part of the contract.
        actual = frozenset(langgraph_forge.__all__)

        assert actual == EXPECTED_PUBLIC_API

    def test_every_exported_symbol_is_importable(self) -> None:
        # If a name is in __all__ but not actually defined on the
        # module, `from langgraph_forge import *` would fail. Catch
        # that at test time, not at first user import.
        missing = [name for name in EXPECTED_PUBLIC_API if not hasattr(langgraph_forge, name)]

        assert missing == []
