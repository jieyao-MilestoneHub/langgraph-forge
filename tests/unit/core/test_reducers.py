"""Tests for langgraph_forge.core.reducers."""

from __future__ import annotations

import pytest

from langgraph_forge.core.reducers import append_unique_reducer, merge_dict_reducer


class TestMergeDictReducerHappyPath:
    def test_no_collision_unions_keys(self) -> None:
        result = merge_dict_reducer({"a": 1}, {"b": 2})

        assert result == {"a": 1, "b": 2}

    def test_right_wins_on_leaf_collision(self) -> None:
        result = merge_dict_reducer({"a": 1}, {"a": 99})

        assert result == {"a": 99}

    def test_recursive_merge_preserves_unaffected_subkeys(self) -> None:
        # Nested dicts merge recursively rather than wholesale-replace.
        result = merge_dict_reducer(
            {"meta": {"created_by": "alice", "tag": "draft"}},
            {"meta": {"tag": "final"}},
        )

        assert result == {"meta": {"created_by": "alice", "tag": "final"}}


class TestMergeDictReducerEmptyInputs:
    def test_empty_left_returns_right(self) -> None:
        assert merge_dict_reducer({}, {"a": 1}) == {"a": 1}

    def test_empty_right_returns_left(self) -> None:
        assert merge_dict_reducer({"a": 1}, {}) == {"a": 1}

    def test_both_empty_returns_empty(self) -> None:
        assert merge_dict_reducer({}, {}) == {}


class TestMergeDictReducerImmutability:
    def test_does_not_mutate_left_argument(self) -> None:
        left = {"a": 1, "nested": {"x": 1}}
        merge_dict_reducer(left, {"a": 2, "nested": {"y": 2}})

        assert left == {"a": 1, "nested": {"x": 1}}

    def test_does_not_mutate_right_argument(self) -> None:
        right = {"a": 2}
        merge_dict_reducer({"a": 1}, right)

        assert right == {"a": 2}


class TestAppendUniqueReducerHappyPath:
    def test_empty_left_returns_right_in_order(self) -> None:
        assert append_unique_reducer([], [1, 2, 3]) == [1, 2, 3]

    def test_disjoint_lists_concatenate(self) -> None:
        assert append_unique_reducer([1, 2], [3, 4]) == [1, 2, 3, 4]

    def test_duplicates_in_right_dropped(self) -> None:
        # Items already in left are not re-added when right re-mentions them.
        assert append_unique_reducer([1, 2, 3], [2, 4, 3]) == [1, 2, 3, 4]


class TestAppendUniqueReducerOrderPreservation:
    def test_left_order_preserved(self) -> None:
        # First-seen wins; left's original order stays intact.
        assert append_unique_reducer([3, 1, 2], [4, 5]) == [3, 1, 2, 4, 5]

    def test_right_order_preserved_for_new_items(self) -> None:
        assert append_unique_reducer([1], [3, 2, 4]) == [1, 3, 2, 4]


class TestAppendUniqueReducerImmutability:
    def test_does_not_mutate_left(self) -> None:
        left = [1, 2]
        append_unique_reducer(left, [3])

        assert left == [1, 2]

    def test_does_not_mutate_right(self) -> None:
        right = [3, 4]
        append_unique_reducer([1, 2], right)

        assert right == [3, 4]


class TestAppendUniqueReducerEdgeCases:
    def test_empty_both_returns_empty(self) -> None:
        assert append_unique_reducer([], []) == []

    def test_unhashable_items_raise(self) -> None:
        # Items must be hashable for de-duplication; surface this clearly
        # rather than silently returning duplicates.
        with pytest.raises(TypeError):
            append_unique_reducer([], [{"unhashable": "dict"}])
