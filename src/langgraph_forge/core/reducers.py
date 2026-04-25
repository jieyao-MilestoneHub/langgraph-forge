"""Non-trivial state-channel reducers.

Reducers we ship are limited to ones users would otherwise mis-write
(silent shallow merge instead of deep merge; silent duplicate
accumulation instead of de-duped append). Trivial reducers that
LangGraph already provides (``add_messages``) or that Python's
standard library covers (``operator.add`` for plain list concat) are
deliberately not duplicated here.
"""

from __future__ import annotations

from typing import Any


def merge_dict_reducer(left: dict[Any, Any], right: dict[Any, Any]) -> dict[Any, Any]:
    """Recursively merge ``right`` into ``left``; right wins on leaf collisions.

    For nested dicts on a colliding key, the merge recurses into the
    sub-dict rather than wholesale-replacing it. Non-dict values
    (including lists) are replaced wholesale by ``right``.

    Neither argument is mutated; a fresh dict is returned.
    """
    result = dict(left)
    for key, right_value in right.items():
        left_value = result.get(key)
        if isinstance(left_value, dict) and isinstance(right_value, dict):
            result[key] = merge_dict_reducer(left_value, right_value)
        else:
            result[key] = right_value
    return result


def append_unique_reducer(left: list[Any], right: list[Any]) -> list[Any]:
    """Concatenate ``right`` onto ``left`` skipping items already present.

    Order is preserved: ``left``'s order is unchanged, and new items
    from ``right`` are appended in the order they first appear there.
    Items must be hashable (we use a set for the membership check); a
    ``TypeError`` surfaces immediately on unhashable input rather than
    falling back to slow O(n*m) ``in`` checks that would silently
    succeed.

    Neither argument is mutated; a fresh list is returned.
    """
    seen = set(left)
    result = list(left)
    for item in right:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
