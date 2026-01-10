from typing import Any

import pytest
from pydantic import ValidationError

from coreason_validator.schemas.tool import ToolCall


def test_valid_tool_call() -> None:
    """Test a valid tool call."""
    tool = ToolCall(tool_name="get_user", arguments={"user_id": 123, "include_profile": True})
    assert tool.tool_name == "get_user"
    assert tool.arguments["user_id"] == 123


def test_strict_tool_name() -> None:
    """Test that tool_name must be a string (strict mode)."""
    with pytest.raises(ValidationError) as exc:
        ToolCall(
            tool_name=123,  # type: ignore
            arguments={},
        )
    # Pydantic v2 strict mode error
    assert "string_type" in str(exc.value)


def test_strict_arguments_type() -> None:
    """Test that arguments must be a dict."""
    with pytest.raises(ValidationError) as exc:
        ToolCall(
            tool_name="test",
            arguments='{"a": 1}',  # type: ignore
        )
    assert "dict_type" in str(exc.value)


def test_sql_injection_simple() -> None:
    """Test SQL injection detection in simple field."""
    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="db_query", arguments={"limit": "DROP TABLE users"})
    assert "Potential SQL injection detected" in str(exc.value)
    assert "DROP TABLE" in str(exc.value)


def test_sql_injection_case_insensitive() -> None:
    """Test SQL injection detection is case insensitive."""
    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="db_query", arguments={"query": "delete  from users"})
    assert "delete  from" in str(exc.value).lower()


def test_sql_injection_nested_dict() -> None:
    """Test SQL injection detection in nested dictionary."""
    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="complex_tool", arguments={"filter": {"where": "UNION SELECT * FROM passwords"}})
    assert "UNION SELECT" in str(exc.value)
    assert "filter.where" in str(exc.value)


def test_sql_injection_list() -> None:
    """Test SQL injection detection in list."""
    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="batch_tool", arguments={"commands": ["safe", "DROP TABLE data"]})
    assert "DROP TABLE" in str(exc.value)
    assert "commands[1]" in str(exc.value)


def test_safe_strings() -> None:
    """Test that normal strings are allowed."""
    tool = ToolCall(tool_name="search", arguments={"query": "tables and chairs"})
    assert tool.arguments["query"] == "tables and chairs"


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError) as exc:
        ToolCall(
            tool_name="test",
            arguments={},
            extra="not allowed",  # type: ignore
        )
    assert "extra_forbidden" in str(exc.value)


# --- New Tests for Edge Cases & Refined Logic ---


def test_false_positive_update() -> None:
    """
    Test that 'update' used in a normal sentence does not trigger validation error.
    Previously this might have failed if logic was just 'UPDATE ' in string.
    """
    tool = ToolCall(tool_name="jira", arguments={"description": "Please update the ticket status."})
    assert tool.arguments["description"] == "Please update the ticket status."


def test_true_positive_update_set() -> None:
    """
    Test that 'UPDATE table SET' triggers the error.
    """
    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="db", arguments={"query": "UPDATE users SET active=0"})
    assert "UPDATE users SET" in str(exc.value)


def test_false_positive_drop() -> None:
    """
    Test 'drop' in normal context.
    """
    tool = ToolCall(tool_name="delivery", arguments={"instruction": "drop the package at the door"})
    assert tool.arguments["instruction"] == "drop the package at the door"


def test_deep_nesting() -> None:
    """
    Test a deeply nested structure to ensure recursion works and finds the injection.
    """
    # Create a deep structure
    deep_args: dict[str, Any] = {"level0": "safe"}
    current = deep_args
    for i in range(1, 20):
        current[f"level{i}"] = {}
        current = current[f"level{i}"]

    current["payload"] = "SELECT * FROM x WHERE id=1 OR 1=1"

    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="deep_check", arguments=deep_args)
    assert "OR 1=1" in str(exc.value)
    # Check if path is roughly correct (implementation detail: string representation might vary)
    assert "level19.payload" in str(exc.value) or "payload" in str(exc.value)


def test_mixed_types_in_list() -> None:
    """
    Test a list containing mixed types (int, None, dict, list, string).
    """
    with pytest.raises(ValidationError) as exc:
        ToolCall(
            tool_name="mixer",
            arguments={
                "data": [
                    1,
                    None,
                    {"a": "safe"},
                    ["nested_list", "DROP TABLE hidden"],  # Injection here
                    True,
                ]
            },
        )

    assert "DROP TABLE" in str(exc.value)
    assert "data[3][1]" in str(exc.value)


def test_newline_handling() -> None:
    """
    Test that newlines do not bypass the regex.
    """
    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="db", arguments={"query": "DROP\nTABLE\nusers"})
    assert "DROP\nTABLE" in str(exc.value) or "Potential SQL injection" in str(exc.value)


def test_comment_dash_dash() -> None:
    """
    Test that double dash comment is caught.
    """
    with pytest.raises(ValidationError) as exc:
        ToolCall(tool_name="db", arguments={"query": "SELECT * FROM users -- ignore rest"})
    assert "--" in str(exc.value)
