# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any, Dict, List

from coreason_validator.schemas.base import CoReasonBaseModel


class DummyModel(CoReasonBaseModel):
    data: Dict[str, Any]


class ListModel(CoReasonBaseModel):
    items: List[str]


class ListOfDictsModel(CoReasonBaseModel):
    items: List[Dict[str, Any]]


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
