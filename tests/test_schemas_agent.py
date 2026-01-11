import pytest
from pydantic import ValidationError

from coreason_validator.schemas.agent import AgentManifest


def test_valid_agent_manifest() -> None:
    """Test creating a valid AgentManifest."""
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config_id="gpt-4",
        max_cost_limit=10.0,
    )
    assert manifest.name == "test-agent"
    assert manifest.version == "1.0.0"
    assert manifest.model_config_id == "gpt-4"
    assert manifest.max_cost_limit == 10.0
    assert manifest.schema_version == "1.0"


def test_invalid_name_pattern() -> None:
    """Test that name must be kebab-case."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="TestAgent",  # Invalid: contains capitals
            version="1.0.0",
            model_config_id="gpt-4",
            max_cost_limit=10.0,
        )
    assert "string_pattern_mismatch" in str(exc.value)


def test_invalid_version_pattern() -> None:
    """Test that version must be SemVer."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0",  # Invalid: missing patch version
            model_config_id="gpt-4",
            max_cost_limit=10.0,
        )
    assert "string_pattern_mismatch" in str(exc.value)


def test_invalid_cost_limit() -> None:
    """Test that max_cost_limit must be > 0."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-4",
            max_cost_limit=0.0,  # Invalid: must be > 0
        )
    assert "greater_than" in str(exc.value)


def test_invalid_schema_version() -> None:
    """Test that schema_version must be '1.0'."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-4",
            max_cost_limit=10.0,
            schema_version="0.9",
        )
    assert "literal_error" in str(exc.value)


def test_extra_fields_forbidden() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config_id="gpt-4",
            max_cost_limit=10.0,
            extra_field="should-fail",  # type: ignore
        )
    assert "extra_forbidden" in str(exc.value)


def test_immutability() -> None:
    """Test that the model is immutable."""
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config_id="gpt-4",
        max_cost_limit=10.0,
    )
    with pytest.raises(ValidationError) as exc:
        manifest.name = "new-name"  # type: ignore[misc]
    assert "frozen_instance" in str(exc.value)


def test_serialization_alias() -> None:
    """Test serialization with alias."""
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config_id="gpt-4",
        max_cost_limit=10.0,
    )
    dumped = manifest.model_dump(by_alias=True)
    assert "model_config" in dumped
    assert "model_config_id" not in dumped
    assert dumped["model_config"] == "gpt-4"


def test_name_edge_cases() -> None:
    """Test edge cases for name pattern."""
    # Valid edge cases
    AgentManifest(
        name="a-b",
        version="1.0.0",
        model_config_id="gpt-4",
        max_cost_limit=1.0,
    )
    AgentManifest(
        name="1-2",
        version="1.0.0",
        model_config_id="gpt-4",
        max_cost_limit=1.0,
    )

    # Invalid edge cases
    with pytest.raises(ValidationError):
        AgentManifest(name="a_b", version="1.0.0", model_config_id="gpt-4", max_cost_limit=1.0)

    with pytest.raises(ValidationError):
        AgentManifest(name="", version="1.0.0", model_config_id="gpt-4", max_cost_limit=1.0)

    with pytest.raises(ValidationError):
        AgentManifest(name="A-b", version="1.0.0", model_config_id="gpt-4", max_cost_limit=1.0)


def test_version_edge_cases() -> None:
    """Test edge cases for version pattern."""
    # Valid (by current regex, though maybe not strict SemVer)
    AgentManifest(
        name="test",
        version="0.0.0",
        model_config_id="gpt-4",
        max_cost_limit=1.0,
    )

    # Invalid
    with pytest.raises(ValidationError):
        AgentManifest(name="test", version="1.0", model_config_id="gpt-4", max_cost_limit=1.0)

    with pytest.raises(ValidationError):
        AgentManifest(name="test", version="1.0.0.", model_config_id="gpt-4", max_cost_limit=1.0)

    with pytest.raises(ValidationError):
        AgentManifest(name="test", version="v1.0.0", model_config_id="gpt-4", max_cost_limit=1.0)


def test_cost_edge_cases() -> None:
    """Test edge cases for cost limit."""
    # Infinity is technically a float > 0.0
    # If we want to ban infinity, we should use allow_inf_nan=False in Field or Config
    # Default pydantic behavior allows it. Let's see if it works.
    manifest = AgentManifest(
        name="test",
        version="1.0.0",
        model_config_id="gpt-4",
        max_cost_limit=float("inf"),
    )
    assert manifest.max_cost_limit == float("inf")

    # NaN comparison
    # NaN > 0.0 is False, so it should fail validation
    with pytest.raises(ValidationError):
        AgentManifest(
            name="test",
            version="1.0.0",
            model_config_id="gpt-4",
            max_cost_limit=float("nan"),
        )
