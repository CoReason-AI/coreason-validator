# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any, Dict, List, Tuple

from coreason_validator.schemas.base import CoReasonBaseModel


class DummyModel(CoReasonBaseModel):
    data: Dict[str, Any]


class ListModel(CoReasonBaseModel):
    items: List[str]


class ListOfDictsModel(CoReasonBaseModel):
    items: List[Dict[str, Any]]


class TupleModel(CoReasonBaseModel):
    items: Tuple[str, ...]


def test_flat_dict_order_independence() -> None:
    """Verify that key order in a flat dictionary does not affect the hash."""
    m1 = DummyModel(data={"a": 1, "b": 2})
    m2 = DummyModel(data={"b": 2, "a": 1})

    assert m1.canonical_hash() == m2.canonical_hash()


def test_nested_dict_order_independence() -> None:
    """Verify that key order in nested dictionaries does not affect the hash."""
    m1 = DummyModel(data={"config": {"host": "localhost", "port": 8080}})
    m2 = DummyModel(data={"config": {"port": 8080, "host": "localhost"}})

    assert m1.canonical_hash() == m2.canonical_hash()


def test_deeply_nested_mixed_order() -> None:
    """Verify deep nesting stability."""
    data1 = {"level1": {"x": 10, "y": {"foo": "bar", "baz": 42}}}
    data2 = {"level1": {"y": {"baz": 42, "foo": "bar"}, "x": 10}}
    m1 = DummyModel(data=data1)
    m2 = DummyModel(data=data2)
    assert m1.canonical_hash() == m2.canonical_hash()


def test_list_order_sensitivity() -> None:
    """Verify that list order DOES affect the hash (lists are ordered sequences)."""
    m1 = ListModel(items=["apple", "banana"])
    m2 = ListModel(items=["banana", "apple"])

    assert m1.canonical_hash() != m2.canonical_hash()


def test_list_of_dicts_key_sorting() -> None:
    """
    Verify that dictionaries INSIDE a list are also key-sorted.
    The order of the list itself matters (checked above), but the keys of dicts inside should not.
    """
    # List is same order, but dict keys inside are different
    m1 = ListOfDictsModel(items=[{"a": 1, "b": 2}, {"x": 10, "y": 20}])
    m2 = ListOfDictsModel(items=[{"b": 2, "a": 1}, {"y": 20, "x": 10}])

    assert m1.canonical_hash() == m2.canonical_hash()


def test_unicode_consistency() -> None:
    """Verify unicode characters are hashed consistently and not escaped."""
    m1 = DummyModel(data={"key": "café"})
    h1 = m1.canonical_hash()

    m2 = DummyModel(data={"key": "café"})
    assert h1 == m2.canonical_hash()


def test_empty_and_null_stability() -> None:
    """Verify stability of empty structures and None."""
    data: Dict[str, Any] = {
        "empty_dict": {},
        "empty_list": [],
        "none_value": None,
        "zero": 0,
        "false": False,
        "empty_string": "",
    }
    # Create two models with different insertion orders for these edge cases
    m1 = DummyModel(data=data)

    data_reversed = {
        "empty_string": "",
        "false": False,
        "zero": 0,
        "none_value": None,
        "empty_list": [],
        "empty_dict": {},
    }
    m2 = DummyModel(data=data_reversed)

    assert m1.canonical_hash() == m2.canonical_hash()


def test_numeric_string_key_sorting() -> None:
    """
    Verify sorting behavior of keys that look like numbers.
    JSON keys are strings. "10" comes before "2" in lexicographical sort.
    """
    # "10" < "2" because '1' < '2'
    data1 = {"2": "value2", "10": "value10"}
    data2 = {"10": "value10", "2": "value2"}

    m1 = DummyModel(data=data1)
    m2 = DummyModel(data=data2)

    assert m1.canonical_hash() == m2.canonical_hash()

    # Just to double check, they should also produce the same hash as the manually sorted version
    # But since we can't see the internal string, we rely on equality.


def test_type_differentiation() -> None:
    """Verify that integer 1 and string '1' hash differently (in values)."""
    # keys are always strings in JSON, but values preserve type (mostly)
    m1 = DummyModel(data={"val": 1})
    m2 = DummyModel(data={"val": "1"})

    assert m1.canonical_hash() != m2.canonical_hash()


def test_tuple_vs_list_stability() -> None:
    """Verify that Tuples are serialized as Lists and hashed consistently."""
    # If a model defines a Tuple, Pydantic serializes it to a JSON Array (List)
    m_tuple = TupleModel(items=("a", "b"))
    m_list = ListModel(items=["a", "b"])

    # The hash should likely be the same because canonical_hash uses model_dump(mode='json')
    # which converts Tuple -> List.
    # Note: Structure of model names doesn't affect hash, only the data (if hash function only dumps data).
    # Wait, canonical_hash in base.py does: `self.model_dump(mode="json")`.
    # It does NOT include the class name in the hash. So strict structural duck-typing applies.

    # We need to verify if field names match. TupleModel has 'items', ListModel has 'items'.
    # So { "items": ["a", "b"] } should be the result for both.

    assert m_tuple.canonical_hash() == m_list.canonical_hash()


def test_complex_nested_scenario() -> None:
    """
    A comprehensive test combining various edge cases:
    - Nested dicts with mixed order
    - Lists of dicts
    - Unicode
    - Empty structures
    - Mixed types
    """
    data1 = {
        "meta": {"version": 1, "author": "Jules"},
        "payload": [
            {"id": "A", "values": [1, 2, 3], "attributes": {"x": None, "y": ""}},
            {"id": "B", "values": [], "attributes": {}},
        ],
        "flags": {"dry_run": False, "verbose": True},
        "tags": ["café", "test"],
    }

    # scrambled order
    data2 = {
        "tags": ["café", "test"],  # List order must be preserved
        "flags": {"verbose": True, "dry_run": False},  # Dict order scrambled
        "payload": [
            {"attributes": {"y": "", "x": None}, "values": [1, 2, 3], "id": "A"},  # keys scrambled
            {"attributes": {}, "id": "B", "values": []},
        ],
        "meta": {"author": "Jules", "version": 1},  # keys scrambled
    }

    m1 = DummyModel(data=data1)
    m2 = DummyModel(data=data2)

    assert m1.canonical_hash() == m2.canonical_hash()
