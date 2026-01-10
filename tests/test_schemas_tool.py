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
        ToolCall(tool_name="db_query", arguments={"query": "delete from users"})
    assert "DELETE FROM" in str(exc.value)


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
