# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any

import pytest
from pydantic import ValidationError

from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.validator import sanitize_inputs, validate_object, validate_tool_call


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
    assert clean["meta"][" key "] == "value"  # Keys are not sanitized in this implementation, only values?
    # Wait, implementation:
    # if isinstance(data, dict): return {k: sanitize_inputs(v) for k, v in data.items()}
    # So keys are NOT sanitized. Values are.

    assert clean["tags"] == ["tag1", "tag2"]


def test_validate_object_with_alias() -> None:
    """
    Test validate_object using string aliases.
    """
    data = {"tool_name": "sql_query", "arguments": {"query": "SELECT * FROM users"}}

    # Test with valid alias
    tool: ToolCall = validate_object(data, "tool")
    assert isinstance(tool, ToolCall)
    assert tool.tool_name == "sql_query"

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
    data = {"tool_name": "sql_query", "arguments": {"query": "SELECT * FROM users"}}
    tool = validate_object(data, ToolCall)
    assert isinstance(tool, ToolCall)


def test_validate_tool_call_wrapper() -> None:
    """
    Test the specific validate_tool_call wrapper.
    """
    data = {"tool_name": "weather", "arguments": {"city": "Paris"}}
    tool = validate_tool_call(data)
    assert isinstance(tool, ToolCall)
    assert tool.tool_name == "weather"
    assert tool.arguments["city"] == "Paris"


def test_validate_tool_call_failure() -> None:
    """
    Test failure in validate_tool_call.
    """
    data = {
        "tool_name": "weather",
        # Missing arguments
    }
    with pytest.raises(ValidationError):
        validate_tool_call(data)


def test_validate_agent_alias() -> None:
    """
    Test validate_object with 'agent' alias.
    """
    data = {
        "schema_version": "1.0",
        "name": "my-agent",
        "version": "1.0.0",
        "model_config": "gpt-4-turbo",
        "max_cost_limit": 5.0,
        "topology": "t.json",
    }
    agent: AgentManifest = validate_object(data, "agent")
    assert isinstance(agent, AgentManifest)
