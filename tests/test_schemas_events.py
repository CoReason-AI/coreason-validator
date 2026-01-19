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

from coreason_validator.schemas.events import GraphEvent, NodeState


def test_valid_graph_event() -> None:
    event = GraphEvent(
        execution_id="exec-123",
        node_id="node-456",
        timestamp=1234567890.0,
        state=NodeState.RUNNING,
        progress=0.5,
        metadata={"key": "value"},
    )
    assert event.state == NodeState.RUNNING
    assert event.progress == 0.5
    assert event.metadata == {"key": "value"}


def test_graph_event_no_metadata() -> None:
    event = GraphEvent(
        execution_id="exec-123", node_id="node-456", timestamp=1234567890.0, state=NodeState.PENDING, progress=0.0
    )
    assert event.metadata is None


def test_invalid_node_state() -> None:
    with pytest.raises(ValidationError):
        GraphEvent(execution_id="exec-123", node_id="node-456", timestamp=1234567890.0, state="INVALID", progress=0.0)
