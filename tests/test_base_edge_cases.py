import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Union

from coreason_validator.schemas.base import CoReasonBaseModel


class ComplexModel(CoReasonBaseModel):
    tags: Set[str]
    numbers: Set[int]
    timestamp: datetime
    uid: uuid.UUID
    mixed_data: Dict[str, Any]
    nested_list: List[Dict[str, Union[int, str]]]


def test_set_determinism() -> None:
    """
    Test that sets are serialized deterministically.
    Pydantic's JSON serialization of sets converts them to lists.
    We need to ensure the order is consistent (sorted) for the hash to be stable.
    """
    # Create two models with sets constructed in different orders
    m1 = ComplexModel(
        tags={"apple", "banana", "cherry"},
        numbers={3, 1, 2},
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        uid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        mixed_data={},
        nested_list=[],
    )
    m2 = ComplexModel(
        tags={"cherry", "apple", "banana"},  # Different insertion order
        numbers={2, 3, 1},
        timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        uid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        mixed_data={},
        nested_list=[],
    )

    # If Pydantic/JSON dump sorts sets, these hashes should be equal.
    # If not, this test will fail, indicating we need a fix in CoReasonBaseModel.
    assert m1.canonical_hash() == m2.canonical_hash()


def test_datetime_and_uuid_consistency() -> None:
    """
    Test that Datetime and UUID serialize consistently.
    """
    uid_str = "12345678-1234-5678-1234-567812345678"
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    m1 = ComplexModel(
        tags=set(),
        numbers=set(),
        timestamp=dt,
        uid=uuid.UUID(uid_str),
        mixed_data={},
        nested_list=[],
    )

    # Verify the hash is stable across multiple calls
    h1 = m1.canonical_hash()
    h2 = m1.canonical_hash()
    assert h1 == h2


def test_deep_nested_structure() -> None:
    """
    Test a complex nested structure.
    """
    m1 = ComplexModel(
        tags={"a"},
        numbers={1},
        timestamp=datetime.now(timezone.utc),
        uid=uuid.uuid4(),
        mixed_data={"key1": "value", "key2": [1, 2, 3], "key3": {"nested": True}},
        nested_list=[{"id": 1, "val": "a"}, {"id": 2, "val": "b"}],
    )

    # Just ensuring it runs without error and returns a hash
    assert isinstance(m1.canonical_hash(), str)


def test_float_behavior() -> None:
    """
    Test float serialization behavior.
    """

    class FloatModel(CoReasonBaseModel):
        val: float

    f1 = FloatModel(val=1.0)
    f2 = FloatModel(val=1)  # int coerced to float

    assert f1.canonical_hash() == f2.canonical_hash()

    f3 = FloatModel(val=1.0000000001)
    assert f1.canonical_hash() != f3.canonical_hash()
