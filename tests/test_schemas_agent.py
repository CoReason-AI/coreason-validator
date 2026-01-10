import pytest
from pydantic import ValidationError

from coreason_validator.schemas.agent import AgentManifest


def test_valid_agent_manifest() -> None:
    """Test creating a valid AgentManifest."""
    manifest = AgentManifest(
        name="test-agent",
        version="1.0.0",
        model_config="gpt-4",
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
            model_config="gpt-4",
            max_cost_limit=10.0,
        )
    assert "string_pattern_mismatch" in str(exc.value)


def test_invalid_version_pattern() -> None:
    """Test that version must be SemVer."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0",  # Invalid: missing patch version
            model_config="gpt-4",
            max_cost_limit=10.0,
        )
    assert "string_pattern_mismatch" in str(exc.value)


def test_invalid_cost_limit() -> None:
    """Test that max_cost_limit must be > 0."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config="gpt-4",
            max_cost_limit=0.0,  # Invalid: must be > 0
        )
    assert "greater_than" in str(exc.value)


def test_invalid_schema_version() -> None:
    """Test that schema_version must be '1.0'."""
    with pytest.raises(ValidationError) as exc:
        AgentManifest(
            name="test-agent",
            version="1.0.0",
            model_config="gpt-4",
            max_cost_limit=10.0,
            schema_version="0.9",  # type: ignore
        )
    assert "literal_error" in str(exc.value)
