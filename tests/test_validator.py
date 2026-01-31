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
from pydantic import ValidationError

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_validator.models import ToolCall
from coreason_validator.validator import sanitize_inputs, validate_object


def test_sanitize_inputs_primitives() -> None:
    """Test sanitization of primitive types."""
    assert sanitize_inputs("  hello  ") == "hello"
    assert sanitize_inputs("null\0byte") == "nullbyte"
    assert sanitize_inputs("\0start") == "start"
    assert sanitize_inputs("end\0") == "end"
    assert sanitize_inputs(123) == 123
    assert sanitize_inputs(1.5) == 1.5
    assert sanitize_inputs(True) is True
    assert sanitize_inputs(None) is None


def test_sanitize_inputs_nested() -> None:
    """Test sanitization of nested dictionaries and lists."""
    data = {"a": "  val  ", "b": ["  item1 ", "item2\0"], "c": {"d": " nested ", "e": [1, "  deep  "]}}
    expected = {"a": "val", "b": ["item1", "item2"], "c": {"d": "nested", "e": [1, "deep"]}}
    assert sanitize_inputs(data) == expected


def test_sanitize_inputs_tuple_set() -> None:
    """Test sanitization of tuples and sets."""
    data_tuple = ("  a  ", "b\0")
    expected_tuple = ("a", "b")
    assert sanitize_inputs(data_tuple) == expected_tuple

    data_set = {"  x  ", "y\0"}
    expected_set = {"x", "y"}
    assert sanitize_inputs(data_set) == expected_set


def test_validate_object_success() -> None:
    """Test successful validation of an AgentDefinition."""
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "my-agent",
            "author": "tester",
            "created_at": "2025-01-01T00:00:00Z"
        },
        "interface": {
            "inputs": {},
            "outputs": {}
        },
        "topology": {
            "steps": [
                {"id": "step1", "description": "start"}
            ],
            "model_config": {
                "model": "gpt-4-turbo",
                "temperature": 0.7
            }
        },
        "dependencies": {},
        "integrity_hash": "a" * 64
    }
    agent = validate_object(data, AgentDefinition)
    assert isinstance(agent, AgentDefinition)
    assert agent.metadata.name == "my-agent"
    assert agent.topology.llm_config.model == "gpt-4-turbo"


def test_validate_object_sanitization_integration() -> None:
    """Test that validate_object correctly sanitizes inputs before validation."""
    data = {"tool_name": "  search  ", "arguments": {"query": "  something  "}}
    tool = validate_object(data, ToolCall)
    assert tool.tool_name == "search"
    assert tool.arguments["query"] == "something"


def test_validate_object_failure_missing_field() -> None:
    """Test validation failure for missing fields."""
    data = {
        "tool_name": "search"
        # Missing arguments
    }
    with pytest.raises(ValidationError) as excinfo:
        validate_object(data, ToolCall)
    assert "arguments" in str(excinfo.value)


def test_validate_object_failure_invalid_type() -> None:
    """Test validation failure for invalid types."""
    data = {"tool_name": "search", "arguments": "not-a-dict"}
    with pytest.raises(ValidationError) as excinfo:
        validate_object(data, ToolCall)
    assert "arguments" in str(excinfo.value)


def test_validate_object_sql_injection() -> None:
    """Test that validate_object catches SQL injection patterns via ToolCall schema."""
    data = {"tool_name": "db_tool", "arguments": {"query": "SELECT * FROM users; DROP TABLE users;"}}
    with pytest.raises(ValidationError, match="Potential SQL injection"):
        validate_object(data, ToolCall)
