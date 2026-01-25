# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import pytest
from coreason_validator.validator import check_compliance


def test_compliance_complex_oneof() -> None:
    """Test oneOf validation (union types)."""
    schema = {
        "type": "object",
        "properties": {
            "result": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "integer"},
                    {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                        "required": ["error"],
                        "additionalProperties": False,
                    },
                ]
            }
        },
        "required": ["result"],
    }

    # Valid cases
    check_compliance({"result": "success"}, schema)
    check_compliance({"result": 42}, schema)
    check_compliance({"result": {"error": "failed"}}, schema)

    # Invalid cases
    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance({"result": 1.5}, schema)  # Float not allowed

    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance({"result": {"unknown": "field"}}, schema)  # additionalProperties: false


def test_compliance_nested_arrays() -> None:
    """Test validation of nested arrays of objects."""
    schema = {
        "type": "object",
        "properties": {
            "users": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}, "tags": {"type": "array", "items": {"type": "string"}}},
                    "required": ["id", "tags"],
                },
            }
        },
    }

    data = {"users": [{"id": 1, "tags": ["admin", "staff"]}, {"id": 2, "tags": []}]}
    check_compliance(data, schema)

    invalid_data = {
        "users": [
            {"id": 1, "tags": ["admin"]},
            {"id": 2, "tags": [123]},  # Invalid tag type
        ]
    }
    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance(invalid_data, schema)


def test_compliance_sanitization_effect() -> None:
    """Test that input sanitization (trimming) works before validation."""
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string", "enum": ["active", "inactive"]}},
        "required": ["status"],
    }

    # Input has whitespace, but sanitization should fix it
    data = {"status": "  active  "}
    check_compliance(data, schema)

    # Input has null byte
    data_null = {"status": "active\0"}
    check_compliance(data_null, schema)


def test_compliance_pattern_matching() -> None:
    """Test regex pattern matching."""
    schema = {"type": "object", "properties": {"version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"}}}

    check_compliance({"version": "1.0.0"}, schema)

    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance({"version": "v1.0"}, schema)


def test_compliance_empty_schema() -> None:
    """Test validation against empty schema (always passes)."""
    schema: dict[str, object] = {}
    check_compliance({"any": "thing"}, schema)


def test_compliance_null_types() -> None:
    """Test nullable fields."""
    schema = {"type": "object", "properties": {"description": {"type": ["string", "null"]}}}

    check_compliance({"description": "text"}, schema)
    check_compliance({"description": None}, schema)

    with pytest.raises(ValueError, match="Compliance check failed"):
        check_compliance({"description": 123}, schema)
