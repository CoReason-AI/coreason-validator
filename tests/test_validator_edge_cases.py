from datetime import datetime
from typing import Any

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
from coreason_manifest.definitions.agent import AgentDefinition
from pydantic import ValidationError

from coreason_validator.validator import sanitize_inputs, validate_object

VALID_HASH = "a" * 64
VALID_UUID = "123e4567-e89b-12d3-a456-426614174000"


def get_valid_agent_data() -> dict[str, Any]:
    return {
        "metadata": {
            "id": VALID_UUID,
            "version": "1.0.0",
            "name": "test-agent",
            "author": "tester",
            "created_at": datetime.utcnow().isoformat(),
        },
        "interface": {
            "inputs": {"type": "object"},
            "outputs": {"type": "object"},
        },
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "node1",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {},
        "integrity_hash": VALID_HASH,
    }


def test_sanitize_inputs_tuples_sets() -> None:
    """Test sanitization of tuples and sets."""
    data_tuple = ("  val  ", "val2\0")
    assert sanitize_inputs(data_tuple) == ("val", "val2")

    data_set = {"  val  ", "val2\0"}
    cleaned_set = sanitize_inputs(data_set)
    assert "val" in cleaned_set
    assert "val2" in cleaned_set
    assert len(cleaned_set) == 2


def test_validate_object_invalid_root_type() -> None:
    """Test validation failure when root data type is incorrect (e.g., list instead of dict)."""
    data = ["not", "a", "dict"]
    with pytest.raises(ValidationError):
        # We ignore type check here to test runtime behavior
        validate_object(data, AgentDefinition)  # type: ignore


def test_validate_object_extra_fields_forbidden() -> None:
    """Test that extra fields cause validation failure (extra='forbid')."""
    data = get_valid_agent_data()
    data["extra_field"] = "should_fail"

    with pytest.raises(ValidationError) as excinfo:
        validate_object(data, AgentDefinition)
    assert "Extra inputs" in str(excinfo.value) or "extra_forbidden" in str(excinfo.value)
    assert "extra_field" in str(excinfo.value)
