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
from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.schemas.topology import TopologyGraph
from coreason_validator.validator import sanitize_inputs, validate_object
from pydantic import ValidationError


def test_sanitize_inputs_tuples_sets() -> None:
    """Test sanitization of tuples and sets."""
    data_tuple = ("  val  ", "val2\0")
    assert sanitize_inputs(data_tuple) == ("val", "val2")

    data_set = {"  val  ", "val2\0"}
    cleaned_set = sanitize_inputs(data_set)
    assert "val" in cleaned_set
    assert "val2" in cleaned_set
    assert len(cleaned_set) == 2


def test_validate_object_topology_cycle() -> None:
    """Test that validate_object correctly catches logical cycles in TopologyGraph."""
    # A -> B -> A cycle
    data = {
        "nodes": [
            {"id": "A", "step_type": "prompt", "next_steps": ["B"]},
            {"id": "B", "step_type": "tool", "next_steps": ["A"]},
        ]
    }
    with pytest.raises(ValidationError) as excinfo:
        validate_object(data, TopologyGraph)
    assert "Cycle detected" in str(excinfo.value)


def test_validate_object_deeply_nested_sql_injection() -> None:
    """Test that validate_object finds SQL injection patterns deep within arguments."""
    data = {
        "tool_name": "db",
        "arguments": {
            "meta": {
                "filters": [
                    {"field": "id", "value": 1},
                    {"field": "name", "value": "DROP TABLE users"},
                ]
            }
        },
    }
    with pytest.raises(ValidationError, match="Potential SQL injection"):
        validate_object(data, ToolCall)


def test_validate_object_invalid_root_type() -> None:
    """Test validation failure when root data type is incorrect (e.g., list instead of dict)."""
    data = ["not", "a", "dict"]
    with pytest.raises(ValidationError):
        # We ignore type check here to test runtime behavior
        validate_object(data, AgentManifest)  # type: ignore


def test_validate_object_extra_fields_forbidden() -> None:
    """Test that extra fields cause validation failure (extra='forbid')."""
    data = {
        "schema_version": "1.0",
        "name": "my-agent",
        "version": "1.0.0",
        "model_config": "gpt-4-turbo",
        "max_cost_limit": 10.0,
        "topology": "t.json",
        "extra_field": "should_fail",
    }
    with pytest.raises(ValidationError) as excinfo:
        validate_object(data, AgentManifest)
    assert "Extra inputs are not permitted" in str(excinfo.value)
    assert "extra_field" in str(excinfo.value)
