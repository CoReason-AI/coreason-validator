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
from pydantic import ValidationError, BaseModel

from coreason_manifest.definitions.message import Message
from coreason_validator.validator import validate_message, validate_object


def test_validate_message_success() -> None:
    """Test successful validation of a message payload."""
    payload = {
        "role": "user",
        "parts": [{"type": "text", "content": "hello"}],
    }
    msg = validate_message(payload)
    assert msg.role == "user"
    assert len(msg.parts) == 1
    assert msg.parts[0].content == "hello"


def test_validate_message_invalid_payload() -> None:
    """Test validation failure with invalid payload."""
    payload = {
        "role": "user",
        # Missing parts
    }
    with pytest.raises(ValidationError):
        validate_message(payload)


def test_validate_message_via_validate_object_alias() -> None:
    """Test validating a message using validate_object with string alias."""
    payload = {
        "role": "user",
        "parts": [{"type": "text", "content": "hello"}],
    }
    obj: BaseModel = validate_object(payload, "message")
    assert isinstance(obj, Message)
    msg: Message = obj
    assert msg.role == "user"


def test_validate_message_sanitization() -> None:
    """Test that message inputs are sanitized."""
    payload = {
        "role": "user",
        "parts": [{"type": "text", "content": "  hello  "}],
    }
    msg = validate_message(payload)
    # content should be trimmed
    assert msg.parts[0].content == "hello"
