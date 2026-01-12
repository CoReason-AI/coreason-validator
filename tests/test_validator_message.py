from datetime import datetime
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_validator.schemas.base import CoReasonBaseModel
from coreason_validator.schemas.message import Message
from coreason_validator.validator import validate_message, validate_object


def test_validate_message_success() -> None:
    """Test successful validation of a message payload."""
    payload = {
        "id": "msg-123",
        "sender": "agent-a",
        "receiver": "agent-b",
        "timestamp": datetime.now(),
        "type": "text",
        "content": {"text": "hello"},
    }
    msg = validate_message(payload)
    assert msg.id == "msg-123"
    assert msg.content["text"] == "hello"


def test_validate_message_invalid_payload() -> None:
    """Test validation failure with invalid payload."""
    payload: Dict[str, Any] = {
        "id": "msg-123",
        # Missing sender, receiver, etc.
    }
    with pytest.raises(ValidationError):
        validate_message(payload)


def test_validate_message_via_validate_object_alias() -> None:
    """Test validating a message using validate_object with string alias."""
    payload = {
        "id": "msg-123",
        "sender": "agent-a",
        "receiver": "agent-b",
        "timestamp": datetime.now(),
        "type": "text",
        "content": {"text": "hello"},
    }
    obj: CoReasonBaseModel = validate_object(payload, "message")
    assert isinstance(obj, Message)
    msg: Message = obj
    # msg type is CoReasonBaseModel at runtime, but we know it's Message
    assert msg.id == "msg-123"


def test_validate_message_sanitization() -> None:
    """Test that message inputs are sanitized."""
    payload = {
        "id": "  msg-123  ",  # Should be trimmed
        "sender": "agent-a",
        "receiver": "agent-b",
        "timestamp": datetime.now(),
        "type": "text",
        "content": {"text": "hello"},
    }
    msg = validate_message(payload)
    assert msg.id == "msg-123"
