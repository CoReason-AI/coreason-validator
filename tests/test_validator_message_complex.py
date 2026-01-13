# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_validator.validator import validate_message


def test_message_whitespace_sanitization_failure() -> None:
    """
    Test that a field containing only whitespace is sanitized to an empty string
    and subsequently fails the min_length=1 validation.
    """
    payload = {
        "id": "   ",  # Becomes ""
        "sender": "agent-a",
        "receiver": "agent-b",
        "timestamp": datetime.now(),
        "type": "text",
        "content": {},
    }
    with pytest.raises(ValidationError) as excinfo:
        validate_message(payload)

    # Check that the error is about 'id' being too short (or empty)
    errors = excinfo.value.errors()
    assert errors[0]["loc"] == ("id",)
    assert "least 1 character" in errors[0]["msg"]


def test_message_null_byte_stripping() -> None:
    """
    Test that null bytes are stripped from strings.
    """
    payload = {
        "id": "msg\0-123",  # Becomes "msg-123"
        "sender": "agent\0-a",  # Becomes "agent-a"
        "receiver": "agent-b",
        "timestamp": datetime.now(),
        "type": "text",
        "content": {"key": "val\0ue"},  # Becomes "value"
    }
    msg = validate_message(payload)
    assert msg.id == "msg-123"
    assert msg.sender == "agent-a"
    assert msg.content["key"] == "value"


def test_message_complex_nested_content() -> None:
    """
    Test a message with deeply nested content structure.
    """
    nested_data = {"level1": {"level2": {"level3": {"data": [1, 2, 3]}}}}
    payload = {
        "id": "msg-deep",
        "sender": "agent-a",
        "receiver": "agent-b",
        "timestamp": datetime.now(),
        "type": "data",
        "content": nested_data,
    }
    msg = validate_message(payload)
    assert msg.content["level1"]["level2"]["level3"]["data"] == [1, 2, 3]


def test_message_cyclic_reference() -> None:
    """
    Test that a cyclic reference in the payload raises RecursionError.
    This confirms that sanitize_inputs (which is recursive) hits the recursion limit.
    """
    cyclic_dict: Dict[str, Any] = {}
    cyclic_dict["self"] = cyclic_dict

    payload = {
        "id": "msg-cycle",
        "sender": "agent-a",
        "receiver": "agent-b",
        "timestamp": datetime.now(),
        "type": "cycle",
        "content": cyclic_dict,
    }

    with pytest.raises(RecursionError):
        validate_message(payload)


def test_message_timestamp_formats() -> None:
    """
    Test various timestamp formats (strings, timezones).
    """
    # ISO String
    ts_str = "2025-01-01T12:00:00Z"
    payload = {
        "id": "msg-ts-1",
        "sender": "a",
        "receiver": "b",
        "timestamp": ts_str,
        "type": "t",
        "content": {},
    }
    msg = validate_message(payload)
    assert msg.timestamp.year == 2025
    assert msg.timestamp.month == 1

    # Future timestamp (should pass as schema doesn't restrict it)
    future_ts = datetime.now(timezone.utc) + timedelta(days=3650)
    payload["timestamp"] = future_ts  # type: ignore[assignment]
    msg_future = validate_message(payload)
    assert msg_future.timestamp == future_ts


def test_message_unicode_emoji() -> None:
    """
    Test valid handling of Unicode characters and Emojis.
    """
    payload = {
        "id": "msg-🚀",
        "sender": "agent-über",
        "receiver": "agent-こんにちは",
        "timestamp": datetime.now(),
        "type": "text",
        "content": {"message": "I ❤️ coding"},
    }
    msg = validate_message(payload)
    assert msg.id == "msg-🚀"
    assert msg.sender == "agent-über"
    assert msg.receiver == "agent-こんにちは"
    assert msg.content["message"] == "I ❤️ coding"


def test_message_strict_type_coercion() -> None:
    """
    Check assumption about type coercion.
    It appears Pydantic V2 or the environment is enforcing strictness for strings.
    We document that int provided for string field raises ValidationError.
    """
    payload = {
        "id": 12345,  # Int provided for String field
        "sender": "a",
        "receiver": "b",
        "timestamp": datetime.now(),
        "type": "t",
        "content": {},
    }
    with pytest.raises(ValidationError) as excinfo:
        validate_message(payload)

    assert "Input should be a valid string" in str(excinfo.value)
