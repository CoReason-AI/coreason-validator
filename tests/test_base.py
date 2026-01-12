from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.schemas.base import CoReasonBaseModel
from coreason_validator.schemas.tool import ToolCall


class SimpleModel(CoReasonBaseModel):
    name: str
    age: int
    active: bool


def test_canonical_hash_determinism() -> None:
    """
    Test that two models with same data but different field definition order
    (simulated by dict insertion order in construction) produce same hash.
    Note: Pydantic fields are ordered by definition, but input dicts can vary.
    The canonical hash implementation sorts keys, so this tests that.
    """
    m1 = SimpleModel(name="Alice", age=30, active=True)
    m2 = SimpleModel(age=30, active=True, name="Alice")

    assert m1.canonical_hash() == m2.canonical_hash()


def test_canonical_hash_nested_determinism() -> None:
    """
    Test that nested structures are also handled deterministically.
    (Requires a model with nested dicts or models).
    """

    class NestedModel(CoReasonBaseModel):
        data: dict[str, int]

    # Python dicts preserve insertion order.
    # json.dumps(sort_keys=True) should fix order differences.
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}

    m1 = NestedModel(data=d1)
    m2 = NestedModel(data=d2)

    assert m1.canonical_hash() == m2.canonical_hash()


def test_canonical_hash_sensitivity() -> None:
    """
    Test that small changes produce different hashes.
    """
    m1 = SimpleModel(name="Alice", age=30, active=True)
    m2 = SimpleModel(name="Alice", age=31, active=True)
    m3 = SimpleModel(name="Bob", age=30, active=True)

    h1 = m1.canonical_hash()
    h2 = m2.canonical_hash()
    h3 = m3.canonical_hash()

    assert h1 != h2
    assert h1 != h3
    assert h2 != h3


def test_canonical_hash_whitespace_handling() -> None:
    """
    Test that:
    1. Semantic whitespace (in values) IS preserved.
    2. Non-semantic whitespace (json formatting) IS removed/standardized.
    """
    # 1. Semantic whitespace
    m1 = SimpleModel(name="Alice ", age=30, active=True)  # Trailing space
    m2 = SimpleModel(name="Alice", age=30, active=True)
    assert m1.canonical_hash() != m2.canonical_hash()

    # 2. Non-semantic whitespace check
    # We can't easily inject non-semantic whitespace into the *input* of the hash function
    # because the user calls .canonical_hash() on the object.
    # But we can verify the hash matches our expectation of 'no whitespace separators'.

    m = SimpleModel(name="A", age=1, active=True)
    # Expected JSON string: {"active":true,"age":1,"name":"A"}
    expected_json = '{"active":true,"age":1,"name":"A"}'
    import hashlib

    expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()

    assert m.canonical_hash() == expected_hash


def test_agent_manifest_inheritance() -> None:
    """
    Verify AgentManifest has canonical_hash and it works.
    """
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=10.0,
        topology="topology.json",
    )
    h = manifest.canonical_hash()
    assert isinstance(h, str)
    assert len(h) == 64  # SHA256 hex digest length


def test_tool_call_inheritance() -> None:
    """
    Verify ToolCall has canonical_hash and it works.
    """
    tool = ToolCall(tool_name="get_user", arguments={"id": 123})
    h = tool.canonical_hash()
    assert isinstance(h, str)
    assert len(h) == 64


def test_unicode_handling() -> None:
    """
    Test that unicode characters are preserved (ensure_ascii=False).
    """
    m1 = SimpleModel(name="Alice ☺", age=30, active=True)

    # If ensure_ascii=True (default), "☺" would be "\u263a"
    # We want it to be bytes of the actual char.

    # Expected JSON: {"active":true,"age":30,"name":"Alice ☺"}
    expected_json = '{"active":true,"age":30,"name":"Alice ☺"}'
    import hashlib

    expected_hash = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()

    assert m1.canonical_hash() == expected_hash
