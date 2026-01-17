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

from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.validator import validate_object


def test_topology_empty_string() -> None:
    """
    Test that an empty string for topology raises a validation error (min_length=1).
    """
    data = {
        "name": "test-agent",
        "version": "1.0.0",
        "model_config": "gpt-4-turbo",
        "max_cost_limit": 1.0,
        "topology": "",
    }
    with pytest.raises(ValidationError) as exc:
        validate_object(data, AgentManifest)
    assert "string_too_short" in str(exc.value)


def test_topology_whitespace_sanitization() -> None:
    """
    Test that topology path is trimmed of whitespace by sanitize_inputs before validation.
    And verify that if it becomes empty after trimming, it fails validation.
    """
    # 1. Valid path with whitespace
    data_valid = {
        "name": "test-agent",
        "version": "1.0.0",
        "model_config": "gpt-4-turbo",
        "max_cost_limit": 1.0,
        "topology": "  path/to/topo.json  ",
    }
    agent = validate_object(data_valid, AgentManifest)
    assert agent.topology == "path/to/topo.json"

    # 2. Whitespace only string (becomes empty)
    data_invalid = {
        "name": "test-agent",
        "version": "1.0.0",
        "model_config": "gpt-4-turbo",
        "max_cost_limit": 1.0,
        "topology": "   ",
    }
    with pytest.raises(ValidationError) as exc:
        validate_object(data_invalid, AgentManifest)
    assert "string_too_short" in str(exc.value)


def test_model_config_case_sensitivity() -> None:
    """
    Test that model_config literal matching is case-sensitive.
    """
    data = {
        "name": "test-agent",
        "version": "1.0.0",
        "model_config": "GPT-4-TURBO",  # Invalid case
        "max_cost_limit": 1.0,
        "topology": "topo.json",
    }
    with pytest.raises(ValidationError) as exc:
        validate_object(data, AgentManifest)
    assert "literal_error" in str(exc.value)


def test_complex_agent_integration() -> None:
    """
    Test a complex scenario with a valid agent manifest structure that includes
    all fields, checking for any unexpected interactions.
    """
    data = {
        "schema_version": "1.0",
        "name": "complex-agent-1",
        "version": "2.10.5",
        "model_config": "claude-3-opus",
        "max_cost_limit": 100.50,
        "topology": "./topologies/nested/complex_graph_v2.json",
    }
    agent = validate_object(data, AgentManifest)
    assert agent.name == "complex-agent-1"
    assert agent.version == "2.10.5"
    assert agent.model_config_id == "claude-3-opus"
    assert agent.max_cost_limit == 100.50
    assert agent.topology == "./topologies/nested/complex_graph_v2.json"


def test_topology_special_characters() -> None:
    """
    Test that topology path accepts special characters (it's just a string).
    """
    special_path = "C:\\Users\\Name\\My Documents\\topo.json"
    data = {
        "name": "windows-agent",
        "version": "1.0.0",
        "model_config": "gpt-4-turbo",
        "max_cost_limit": 1.0,
        "topology": special_path,
    }
    agent = validate_object(data, AgentManifest)
    assert agent.topology == special_path


def test_model_config_alternative_literal() -> None:
    """
    Test that the other allowed literal value works.
    """
    data = {
        "name": "opus-agent",
        "version": "1.0.0",
        "model_config": "claude-3-opus",
        "max_cost_limit": 50.0,
        "topology": "topo.json",
    }
    agent = validate_object(data, AgentManifest)
    assert agent.model_config_id == "claude-3-opus"
