import pytest
from coreason_validator.validator import check_compliance


def test_check_compliance_valid() -> None:
    """Test that valid data passes compliance check."""
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 0}},
        "required": ["name", "age"],
    }
    data = {"name": "Alice", "age": 30}

    # Should not raise exception
    check_compliance(data, schema)


def test_check_compliance_invalid_type() -> None:
    """Test that data with invalid type raises ValueError."""
    schema = {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    data = {"name": "Alice", "age": "thirty"}

    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance(data, schema)


def test_check_compliance_missing_required() -> None:
    """Test that missing required field raises ValueError."""
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    }
    data = {"name": "Alice"}

    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance(data, schema)


def test_check_compliance_nested_error() -> None:
    """Test that nested validation errors are reported correctly."""
    schema = {
        "type": "object",
        "properties": {"user": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
    }
    data = {"user": {"name": "Bob"}}  # Missing 'id'

    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance(data, schema)


def test_check_compliance_invalid_schema() -> None:
    """Test that providing an invalid schema raises ValueError (or appropriate error from jsonschema)."""
    # Note: check_compliance assumes the schema is a valid dict structure,
    # but jsonschema might raise SchemaError if the schema itself is invalid.
    # However, strict compliance check focuses on instance vs schema.
    # Let's see how jsonschema handles garbage schema.
    schema = {"type": "unknown_type"}
    data = {"foo": "bar"}

    from jsonschema.exceptions import SchemaError

    # Depending on implementation, it might re-raise as ValueError or let SchemaError bubble up.
    # The requirement says "Logic: validator.check_compliance(agent_output_json, target_schema_json)"
    # Usually we expect it to fail if schema is bad.

    with pytest.raises((ValueError, SchemaError)):
        check_compliance(data, schema)
