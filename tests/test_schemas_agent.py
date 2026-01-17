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


def test_valid_agent_manifest() -> None:
    """Test creating a valid AgentManifest."""
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=10.0,
        topology="path/to/topology.json",
    )
    assert manifest.name == "test-agent"
    assert manifest.version == "1.0.0"
    assert manifest.model_config_id == "gpt-4-turbo"
    assert manifest.max_cost_limit == 10.0
    assert manifest.schema_version == "1.0"
    assert manifest.topology == "path/to/topology.json"
    assert manifest.temperature == 0.7  # Default check


def test_invalid_name_pattern() -> None:
    """Test that name must be kebab-case."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="TestAgent",  # Invalid: contains capitals
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=10.0,
            topology="topo.json",
        )
    assert "string_pattern_mismatch" in str(exc.value)


def test_invalid_version_pattern() -> None:
    """Test that version must be SemVer."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0",  # Invalid: missing patch version
            model_config_id="gpt-4-turbo",
            max_cost_limit=10.0,
            topology="topo.json",
        )
    assert "string_pattern_mismatch" in str(exc.value)


def test_invalid_cost_limit() -> None:
    """Test that max_cost_limit must be > 0."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=0.0,  # Invalid: must be > 0
            topology="topo.json",
        )
    assert "greater_than" in str(exc.value)


def test_invalid_model_config() -> None:
    """Test that model_config must be one of the allowed literals."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-3.5-turbo",  # Invalid: not in allowed list
            max_cost_limit=10.0,
            topology="topo.json",
        )
    assert "literal_error" in str(exc.value)
    # Check that valid options are mentioned in error message (optional, depends on Pydantic version)


def test_missing_topology() -> None:
    """Test that topology field is required."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(  # type: ignore[call-arg]
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=10.0,
            # Missing topology
        )
    assert "topology" in str(exc.value)
    assert "Field required" in str(exc.value)


def test_invalid_schema_version() -> None:
    """Test that schema_version must be '1.0'."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=10.0,
            topology="topo.json",
            schema_version="0.9",
        )
    assert "literal_error" in str(exc.value)


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=10.0,
            topology="topo.json",
            extra_field="should-fail",  # type: ignore
        )
    assert "extra_forbidden" in str(exc.value)


def test_immutability() -> None:
    """Test that the model is immutable."""
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=10.0,
        topology="topo.json",
    )
    with pytest.raises(ValidationError) as exc:
        manifest.name = "new-name"  # type: ignore[misc]
    assert "frozen_instance" in str(exc.value)


def test_serialization_alias() -> None:
    """Test serialization with alias."""
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=10.0,
        topology="topo.json",
    )
    dumped = manifest.model_dump(by_alias=True)
    assert "model_config" in dumped
    assert "model_config_id" not in dumped
    assert dumped["model_config"] == "gpt-4-turbo"


def test_name_edge_cases() -> None:
    """Test edge cases for name pattern."""
    # Valid edge cases
    AgentManifest(
        name="a-b",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
    )
    AgentManifest(
        name="1-2",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
    )

    # Invalid edge cases
    with pytest.raises(ValidationError):
        AgentManifest(
            name="a_b",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
        )

    with pytest.raises(ValidationError):
        AgentManifest(
            name="",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
        )

    with pytest.raises(ValidationError):
        AgentManifest(
            name="A-b",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
        )


def test_version_edge_cases() -> None:
    """Test edge cases for version pattern."""
    # Valid (by current regex, though maybe not strict SemVer)
    AgentManifest(
        name="test",
        version="0.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t.json",
    )

    # Invalid
    with pytest.raises(ValidationError):
        AgentManifest(
            name="test",
            version="1.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
        )

    with pytest.raises(ValidationError):
        AgentManifest(
            name="test",
            version="1.0.0.",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
        )

    with pytest.raises(ValidationError):
        AgentManifest(
            name="test",
            version="v1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t.json",
        )


def test_cost_edge_cases() -> None:
    """Test edge cases for cost limit."""
    # Infinity is technically a float > 0.0
    # If we want to ban infinity, we should use allow_inf_nan=False in Field or Config
    # Default pydantic behavior allows it. Let's see if it works.
    manifest = AgentManifest(
        name="test",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=float("inf"),
        topology="t.json",
    )
    assert manifest.max_cost_limit == float("inf")

    # NaN comparison
    # NaN > 0.0 is False, so it should fail validation
    with pytest.raises(ValidationError):
        AgentManifest(
            name="test",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=float("nan"),
            topology="t.json",
        )


def test_temperature_validation() -> None:
    """Test validation logic for the temperature field."""
    # Valid Cases
    m1 = AgentManifest(
        name="t1",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t",
        temperature=0.0,
    )
    assert m1.temperature == 0.0

    m2 = AgentManifest(
        name="t2",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t",
        temperature=1.0,
    )
    assert m2.temperature == 1.0

    m3 = AgentManifest(
        name="t3",
        version="1.0.0",
        model_config_id="gpt-4-turbo",
        max_cost_limit=1.0,
        topology="t",
        temperature=0.5,
    )
    assert m3.temperature == 0.5

    # Invalid Cases (Out of range)
    with pytest.raises(ValidationError) as exc_low:
        AgentManifest(
            name="t4",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t",
            temperature=-0.1,
        )
    assert "greater_than_equal" in str(exc_low.value)

    with pytest.raises(ValidationError) as exc_high:
        AgentManifest(
            name="t5",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t",
            temperature=1.1,
        )
    assert "less_than_equal" in str(exc_high.value)

    # Invalid Type
    with pytest.raises(ValidationError) as exc_type:
        AgentManifest(
            name="t6",
            version="1.0.0",
            model_config_id="gpt-4-turbo",
            max_cost_limit=1.0,
            topology="t",
            temperature="high",
        )
    # Pydantic V2 message for float type error is "Input should be a valid number"
    assert "float_parsing" in str(exc_type.value) or "Input should be a valid number" in str(exc_type.value)
