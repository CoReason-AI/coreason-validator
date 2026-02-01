# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from datetime import datetime
from typing import Any

import pytest
from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.message import ToolCallRequestPart as ToolCall
from pydantic import ValidationError

from coreason_validator.validator import sanitize_inputs, validate_object, validate_tool_call

VALID_HASH = "a" * 64
VALID_UUID = "123e4567-e89b-12d3-a456-426614174000"


def get_valid_agent_data() -> dict[str, Any]:
    return {
        "metadata": {
            "id": VALID_UUID,
            "version": "1.0.0",
            "name": "test-agent",
            "author": "tester",
            "created_at": datetime.utcnow().isoformat(),
        },
        "interface": {
            "inputs": {"type": "object"},
            "outputs": {"type": "object"},
        },
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "node1",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {},
        "integrity_hash": VALID_HASH,
    }


def test_sanitize_inputs() -> None:
    """
    Test that inputs are properly sanitized.
    """
    data = {
        "name": " Alice ",  # whitespace
        "bio": "Hello\0World",  # null byte
        "meta": {" key ": " value\0 "},
        "tags": [" tag1 ", " tag2\0"],
    }
    clean = sanitize_inputs(data)
    assert clean["name"] == "Alice"
    assert clean["bio"] == "HelloWorld"
    assert clean["meta"][" key "] == "value"  # Keys are not sanitized
    assert clean["tags"] == ["tag1", "tag2"]


def test_validate_object_with_alias() -> None:
    """
    Test validate_object using string aliases.
    """
    data = {"type": "tool_call", "name": "sql_query", "arguments": {"query": "SELECT * FROM users"}}

    # Test with valid alias
    tool: ToolCall = validate_object(data, "tool")
    assert isinstance(tool, ToolCall)
    assert tool.name == "sql_query"

    # Test with case-insensitive alias
    tool2: ToolCall = validate_object(data, "TOOL")
    assert isinstance(tool2, ToolCall)

    # Test with invalid alias
    with pytest.raises(ValueError, match="Unknown schema type alias"):
        validate_object(data, "unknown_alias")


def test_validate_object_invalid_type() -> None:
    """
    Test validate_object with invalid schema_type (not class or string).
    """
    data: dict[str, Any] = {}
    with pytest.raises(ValueError, match="Invalid schema_type argument"):
        validate_object(data, 123)  # type: ignore


def test_validate_object_with_class() -> None:
    """
    Test validate_object using Class.
    """
    data = {"type": "tool_call", "name": "sql_query", "arguments": {"query": "SELECT * FROM users"}}
    tool = validate_object(data, ToolCall)
    assert isinstance(tool, ToolCall)


def test_validate_tool_call_wrapper() -> None:
    """
    Test the specific validate_tool_call wrapper.
    """
    data = {"type": "tool_call", "name": "weather", "arguments": {"city": "Paris"}}
    tool = validate_tool_call(data)
    assert isinstance(tool, ToolCall)
    assert tool.name == "weather"
    assert tool.arguments["city"] == "Paris"


def test_validate_tool_call_failure() -> None:
    """
    Test failure in validate_tool_call.
    """
    data = {
        "type": "tool_call",
        "name": "weather",
        # Missing arguments
    }
    with pytest.raises(ValidationError):
        validate_tool_call(data)


def test_validate_agent_alias() -> None:
    """
    Test validate_object with 'agent' alias.
    """
    data = get_valid_agent_data()
    agent: AgentDefinition = validate_object(data, "agent")
    assert isinstance(agent, AgentDefinition)
