# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_validator.validator import validate_message


def test_message_whitespace_sanitization() -> None:
    """
    Test that a field containing only whitespace is sanitized to an empty string.
    """
    payload = {
        "role": "user",
        "parts": [{"type": "text", "content": "   "}],
        "name": "   ",  # Becomes ""
    }
    msg = validate_message(payload)
    assert msg.parts[0].content == ""
    assert msg.name == ""


def test_message_null_byte_stripping() -> None:
    """
    Test that null bytes are stripped from strings.
    """
    payload = {
        "role": "user",
        "name": "name\0-123",  # Becomes "name-123"
        "parts": [{"type": "text", "content": "val\0ue"}],
    }
    msg = validate_message(payload)
    assert msg.name == "name-123"
    assert msg.parts[0].content == "value"


def test_message_cyclic_reference() -> None:
    """
    Test that a cyclic reference in the payload raises RecursionError.
    This confirms that sanitize_inputs (which is recursive) hits the recursion limit.
    """
    cyclic_dict: Dict[str, Any] = {}
    cyclic_dict["self"] = cyclic_dict

    # Use a tool call part which allows Any in arguments
    payload = {
        "role": "assistant",
        "parts": [
            {
                "type": "tool_call",
                "name": "foo",
                "arguments": cyclic_dict
            }
        ],
    }

    with pytest.raises(RecursionError):
        validate_message(payload)


def test_message_unicode_emoji() -> None:
    """
    Test valid handling of Unicode characters and Emojis.
    """
    payload = {
        "role": "user",
        "name": "agent-🚀",
        "parts": [{"type": "text", "content": "I ❤️ coding"}],
    }
    msg = validate_message(payload)
    assert msg.name == "agent-🚀"
    assert msg.parts[0].content == "I ❤️ coding"


def test_message_strict_type_coercion() -> None:
    """
    Check assumption about type coercion.
    It appears Pydantic V2 or the environment is enforcing strictness for strings.
    We document that int provided for string field raises ValidationError.
    """
    payload = {
        "role": "user",
        "name": 12345,  # Int provided for String field
        "parts": [{"type": "text", "content": "hello"}],
    }
    with pytest.raises(ValidationError) as excinfo:
        validate_message(payload)

    assert "Input should be a valid string" in str(excinfo.value)
