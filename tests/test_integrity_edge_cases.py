from typing import Any, Dict, List, Optional

from coreason_validator.schemas.base import CoReasonBaseModel
from pydantic import ConfigDict


class EdgeCaseModel(CoReasonBaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    description: str
    matrix: List[List[Any]]
    meta: Optional[Dict[str, Any]] = None


def test_list_order_sensitivity() -> None:
    """
    Edge Case: Lists in JSON are ordered.
    canonical_hash MUST return DIFFERENT hashes for different list orders.
    """
    m1 = EdgeCaseModel(description="A", matrix=[[1, 2], [3, 4]])
    m2 = EdgeCaseModel(description="A", matrix=[[2, 1], [3, 4]])  # Inner list changed
    m3 = EdgeCaseModel(description="A", matrix=[[3, 4], [1, 2]])  # Outer list changed

    h1 = m1.canonical_hash()
    h2 = m2.canonical_hash()
    h3 = m3.canonical_hash()

    assert h1 != h2
    assert h1 != h3
    assert h2 != h3


def test_dict_key_insensitivity_inside_lists() -> None:
    """
    Edge Case: Dictionaries INSIDE lists must still be key-sorted.
    """
    # [{"a": 1, "b": 2}] vs [{"b": 2, "a": 1}]
    m1 = EdgeCaseModel(description="B", matrix=[[{"a": 1, "b": 2}]])
    m2 = EdgeCaseModel(description="B", matrix=[[{"b": 2, "a": 1}]])

    assert m1.canonical_hash() == m2.canonical_hash()


def test_unicode_stability() -> None:
    """
    Edge Case: Unicode characters should be hashed consistently.
    """
    # Using Emoji and Kanji
    text = "Hello 🌍 -> 世界"
    m1 = EdgeCaseModel(description=text, matrix=[])
    m2 = EdgeCaseModel(description=text, matrix=[])

    assert m1.canonical_hash() == m2.canonical_hash()

    # Ensure it doesn't crash or error
    assert len(m1.canonical_hash()) == 64


def test_empty_structures() -> None:
    """
    Edge Case: Empty lists and dicts should be handled gracefully.
    """
    m1 = EdgeCaseModel(description="Empty", matrix=[], meta={})
    m2 = EdgeCaseModel(description="Empty", matrix=[], meta={})

    assert m1.canonical_hash() == m2.canonical_hash()

    # Verify strictness: None != {}
    m3 = EdgeCaseModel(description="Empty", matrix=[], meta=None)
    # Note: In Pydantic v2, if field is Optional, None is omitted by exclude_none?
    # Or included as null?
    # CoReasonBaseModel uses model_dump(mode='json'). Default is include None.

    assert m1.canonical_hash() != m3.canonical_hash()


def test_deep_nesting_mixed_types() -> None:
    """
    Edge Case: Deeply nested structure with mixed ints, strings, bools.
    """
    data = {"level1": {"level2": [{"k": "v", "flag": True, "num": 1}, {"k": "v2", "flag": False, "num": 0}]}}

    m1 = EdgeCaseModel(description="Deep", matrix=[], meta=data)

    # Reorder keys in deep dict
    data_reordered = {
        "level1": {
            "level2": [
                {"num": 1, "flag": True, "k": "v"},  # Reordered
                {"num": 0, "k": "v2", "flag": False},  # Reordered
            ]
        }
    }
    m2 = EdgeCaseModel(description="Deep", matrix=[], meta=data_reordered)

    assert m1.canonical_hash() == m2.canonical_hash()
