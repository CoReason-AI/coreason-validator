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

import pytest
from coreason_validator.schemas.message import Message
from pydantic import ValidationError


def test_message_valid_creation() -> None:
    """Test creating a valid Message instance."""
    msg = Message(
        id="msg-123",
        sender="agent-a",
        receiver="agent-b",
        timestamp=datetime.now(),
        type="text",
        content={"text": "Hello world"},
    )
    assert msg.id == "msg-123"
    assert msg.sender == "agent-a"
    assert msg.receiver == "agent-b"
    assert msg.type == "text"
    assert msg.content == {"text": "Hello world"}
    assert msg.schema_version == "1.0"


def test_message_canonical_hash() -> None:
    """Test that Message supports canonical hashing."""
    ts = datetime(2025, 1, 1, 12, 0, 0)
    msg1 = Message(
        id="msg-1",
        sender="a",
        receiver="b",
        timestamp=ts,
        type="test",
        content={"b": 2, "a": 1},
    )
    msg2 = Message(
        id="msg-1",
        sender="a",
        receiver="b",
        timestamp=ts,
        type="test",
        content={"a": 1, "b": 2},  # Different order
    )

    # Hash should be consistent regardless of dict key order
    assert msg1.canonical_hash() == msg2.canonical_hash()
    assert len(msg1.canonical_hash()) == 64


def test_message_immutability() -> None:
    """Test that Message is immutable (frozen)."""
    msg = Message(
        id="msg-1",
        sender="a",
        receiver="b",
        timestamp=datetime.now(),
        type="test",
        content={},
    )
    with pytest.raises(ValidationError):
        msg.id = "new-id"  # type: ignore


def test_message_missing_fields() -> None:
    """Test validation errors for missing fields."""
    with pytest.raises(ValidationError) as excinfo:
        Message(id="msg-1")  # type: ignore

    errors = excinfo.value.errors()
    missing_fields = [e["loc"][0] for e in errors]
    assert "sender" in missing_fields
    assert "receiver" in missing_fields
    assert "timestamp" in missing_fields
    assert "type" in missing_fields
    assert "content" in missing_fields


def test_message_invalid_types() -> None:
    """Test validation errors for invalid types."""
    with pytest.raises(ValidationError):
        Message(
            id=123,  # Should be string # type: ignore
            sender="a",
            receiver="b",
            timestamp="not-a-datetime",  # Should be datetime # type: ignore
            type="test",
            content="not-a-dict",  # Should be dict # type: ignore
        )


def test_message_empty_strings() -> None:
    """Test constraints on string length."""
    with pytest.raises(ValidationError):
        Message(
            id="",
            sender="a",
            receiver="b",
            timestamp=datetime.now(),
            type="test",
            content={},
        )
