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


def test_temperature_precision_edges() -> None:
    """Test floating point precision edge cases for temperature."""
    # Just within bounds
    AgentManifest(
        name="test",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
        temperature=0.0000000000001,
    )
    AgentManifest(
        name="test",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
        temperature=0.9999999999999,
    )

    # Just outside bounds (epsilon)
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
            temperature=1.0000000000001,
        )
    assert "less_than_equal" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
            temperature=-0.0000000000001,
        )
    assert "greater_than_equal" in str(exc.value)


def test_temperature_scientific_notation() -> None:
    """Test scientific notation inputs for temperature."""
    # Valid
    m1 = AgentManifest(
        name="test",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
        temperature=1e-1,  # 0.1
    )
    assert m1.temperature == 0.1

    m2 = AgentManifest(
        name="test",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
        temperature=1e-10,  # Very small positive
    )
    assert m2.temperature == 1e-10

    # Invalid (too large)
    with pytest.raises(ValidationError):
        AgentManifest(
            name="test",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
            temperature=1e1,  # 10.0
        )


def test_temperature_string_coercion() -> None:
    """
    Test string coercion behavior.
    Since strict=True is not set on AgentManifest, Pydantic should coerce numeric strings.
    """
    m = AgentManifest(
        name="test",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
        temperature="0.5",
    )
    assert m.temperature == 0.5
    assert isinstance(m.temperature, float)

    # Invalid string
    with pytest.raises(ValidationError):
        AgentManifest(
            name="test",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
            temperature="hot",
        )


def test_temperature_explicit_none() -> None:
    """Test that explicit None is rejected (field is not Optional)."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
            temperature=None,
        )
    assert "type_error" in str(exc.value) or "Input should be a valid number" in str(exc.value)


def test_complex_instantiation_with_defaults() -> None:
    """Test instantiation within a complex structure or ensuring no side effects."""
    # Validating that providing a dictionary with missing temperature uses default
    data = {
        "name": "complex-agent",
        "version": "2.0.0",
        "model_config": "claude-3-opus",
        "max_cost_limit": 50.0,
        "topology": "complex/topo.yaml",
    }
    m = AgentManifest(**data)
    assert m.temperature == 0.7
    assert m.model_config_id == "claude-3-opus"
