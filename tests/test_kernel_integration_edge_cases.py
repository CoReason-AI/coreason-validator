# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

import pytest
from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.topology import GraphTopology
from pydantic import ValidationError

from coreason_validator.validator import validate_object

# Constants
VALID_SHA256 = "a" * 64
VALID_UUID = str(uuid4())


def get_base_agent_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": VALID_UUID,
            "version": "1.0.0",
            "name": "test-agent",
            "author": "tester",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "requires_auth": False,
        },
        "interface": {
            "inputs": {"type": "object"},
            "outputs": {"type": "object"},
            "injected_params": [],
        },
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {},
        "integrity_hash": VALID_SHA256,
    }


def test_agent_integrity_hash_validation() -> None:
    """
    Test that the integrity_hash field strictly enforces SHA256 hex format.
    """
    data = get_base_agent_data()

    # Case 1: Invalid length (too short)
    data["integrity_hash"] = "a" * 63
    with pytest.raises(ValidationError) as exc:
        validate_object(data, AgentDefinition)
    assert "string_pattern_mismatch" in str(exc.value)

    # Case 2: Invalid characters (non-hex)
    data["integrity_hash"] = "z" * 64
    with pytest.raises(ValidationError) as exc:
        validate_object(data, AgentDefinition)
    assert "string_pattern_mismatch" in str(exc.value)

    # Case 3: Uppercase hex (should pass if regex allows A-F)
    data["integrity_hash"] = "A" * 64
    agent = validate_object(data, AgentDefinition)
    assert agent.integrity_hash == "A" * 64


def test_agent_semver_validation() -> None:
    """
    Test strict Semantic Versioning enforcement on AgentDefinition.
    """
    data = get_base_agent_data()

    # Invalid: Not SemVer
    data["metadata"]["version"] = "v1"
    with pytest.raises(ValidationError) as exc:
        validate_object(data, AgentDefinition)
    # Pydantic regex error
    assert "string_pattern_mismatch" in str(exc.value)

    # Valid: Standard SemVer
    data["metadata"]["version"] = "1.0.0"
    agent = validate_object(data, AgentDefinition)
    assert agent.metadata.version == "1.0.0"

    # Valid: With pre-release
    data["metadata"]["version"] = "1.0.0-beta.1"
    validate_object(data, AgentDefinition)


def test_agent_auth_requirement_logic() -> None:
    """
    Test the model validator logic: if requires_auth is True, user_context must be injected.
    """
    data = get_base_agent_data()
    data["metadata"]["requires_auth"] = True
    # Missing 'user_context' in injected_params

    with pytest.raises(ValidationError) as exc:
        validate_object(data, AgentDefinition)

    # Check for the specific error message defined in AgentDefinition.validate_auth_requirements
    assert "Agent requires authentication but 'user_context' is not an injected parameter" in str(exc.value)

    # Fix it
    data["interface"]["injected_params"] = ["user_context"]
    validate_object(data, AgentDefinition)


def test_topology_node_discriminator_failure() -> None:
    """
    Test that GraphTopology fails when a node has an unknown or missing 'type'.
    """
    data = {
        "nodes": [
            {
                "id": "node1",
                # Missing 'type', or invalid type
                "type": "unknown_magic_node",
                "some_field": "value",
            }
        ],
        "edges": [],
        "state_schema": {"data_schema": {}, "persistence": "memory"},
    }

    with pytest.raises(ValidationError) as exc:
        validate_object(data, GraphTopology)

    # Pydantic V2 discriminator error usually mentions the tag
    err_str = str(exc.value)
    expected_msg = "Input tag 'unknown_magic_node' found using 'type'"
    assert expected_msg in err_str or "Input should be a valid dictionary" in err_str
    # Or it might list allowed values for the discriminator


def test_topology_duplicate_node_ids() -> None:
    """
    Test that duplicate Node IDs in AgentRuntimeConfig are rejected.
    (Note: This validation is on AgentRuntimeConfig, which wraps nodes/edges in AgentDefinition)
    """
    data = get_base_agent_data()
    data["config"]["nodes"] = [
        {"type": "agent", "id": "node1", "agent_name": "a1"},
        {"type": "agent", "id": "node1", "agent_name": "a2"},  # Duplicate ID
    ]

    with pytest.raises(ValidationError) as exc:
        validate_object(data, AgentDefinition)

    assert "Duplicate node IDs found" in str(exc.value)
