# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import tempfile
from pathlib import Path
from typing import Any, Iterator

import pytest
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.validator import sanitize_inputs, validate_file, validate_object, validate_tool_call
from pydantic import ValidationError


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def test_validate_object_alias_variations() -> None:
    """
    Test various alias formats for validate_object.
    """
    data = {"tool_name": "t", "arguments": {}}

    # Mixed case (Should pass)
    assert isinstance(validate_object(data, "TooL"), ToolCall)

    # Wrong schema for data (Should raise ValidationError)
    with pytest.raises(ValidationError):
        validate_object(data, "AGENT")

    # Whitespace (Should fail)
    # " tool " -> lower() is " tool ". key is "tool". No match.
    with pytest.raises(ValueError, match="Unknown schema type alias"):
        validate_object(data, " tool ")

    # Empty string (Should fail)
    with pytest.raises(ValueError, match="Unknown schema type alias"):
        validate_object(data, "")


def test_sanitize_inputs_complex_types() -> None:
    """
    Test sanitize_inputs with various Python types.
    """
    data = {
        "int": 123,
        "float": 12.34,
        "bool": True,
        "none": None,
        "tuple": ("  a  ", 1),
        "set": {"  b  ", 2},
        "list": ["  c  ", 3],
        "nested": {"deep": ("  d  ",)},
    }

    clean = sanitize_inputs(data)

    assert clean["int"] == 123
    assert clean["float"] == 12.34
    assert clean["bool"] is True
    assert clean["none"] is None
    assert clean["tuple"] == ("a", 1)
    assert clean["set"] == {"b", 2}
    assert clean["list"] == ["c", 3]
    assert clean["nested"]["deep"] == ("d",)


def test_sanitize_inputs_recursion() -> None:
    """
    Test that sanitize_inputs raises RecursionError on cyclic data.
    """
    # Create cycle
    data: dict[str, Any] = {}
    data["self"] = data

    # Depending on system, recursion limit varies.
    # We expect RecursionError.
    with pytest.raises(RecursionError):
        sanitize_inputs(data)


def test_validate_file_with_cyclic_data(temp_dir: Path) -> None:
    """
    Test validating a file that creates a cycle (via YAML anchors).
    Should return a ValidationResult with error, not crash.
    """
    p = temp_dir / "cycle_test.yaml"
    # YAML cycle: root points to itself
    p.write_text("&root { next: *root }")

    # validate_file catches RecursionError
    result = validate_file(p, "agent")

    assert not result.is_valid
    # The error message should mention recursion
    assert any("recursion" in str(e).lower() for e in result.errors)


def test_validate_tool_call_deep_injection() -> None:
    """
    Test validate_tool_call wrapper catches deep injection.
    """
    data = {
        "tool_name": "db_ops",
        "arguments": {
            "query_params": {
                "where": [
                    {"col": "id", "val": 1},
                    {"col": "name", "val": "foo OR 1=1"},  # Injection
                ]
            }
        },
    }

    with pytest.raises(ValidationError, match="Potential SQL injection"):
        validate_tool_call(data)


def test_validate_object_keys_are_not_sanitized() -> None:
    """
    Verify that keys are NOT sanitized, only values.
    This is important behavior to document.
    """
    # Key has whitespace
    data = {"  key  ": "  value  "}
    clean = sanitize_inputs(data)

    # Key is preserved exactly
    assert "  key  " in clean
    # Value is trimmed
    assert clean["  key  "] == "value"
