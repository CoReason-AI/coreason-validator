# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import json
import tempfile
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import patch

import pytest
import yaml
from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.topology import Topology
from coreason_manifest.recipes import RecipeManifest

from coreason_validator.validator import validate_file


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def valid_agent_data() -> dict[str, Any]:
    return {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "test-agent",
            "author": "tester",
            "created_at": "2025-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"steps": [{"id": "s1"}], "model_config": {"model": "gpt-4-turbo", "temperature": 0.7}},
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }


def test_validate_file_json_success(temp_dir: Path, valid_agent_data: dict[str, Any]) -> None:
    """Test validating a valid JSON file."""
    file_path = temp_dir / "agent.json"
    file_path.write_text(json.dumps(valid_agent_data))

    result = validate_file(file_path, AgentDefinition)
    assert result.is_valid
    assert result.model is not None
    assert isinstance(result.model, AgentDefinition)
    assert result.model.metadata.name == "test-agent"
    assert not result.errors


def test_validate_file_yaml_success(temp_dir: Path, valid_agent_data: dict[str, Any]) -> None:
    """Test validating a valid YAML file."""
    valid_agent_data["metadata"]["name"] = "test-agent-yaml"
    file_path = temp_dir / "agent.yaml"
    file_path.write_text(yaml.dump(valid_agent_data))

    result = validate_file(file_path, AgentDefinition)
    assert result.is_valid
    assert isinstance(result.model, AgentDefinition)
    assert result.model.metadata.name == "test-agent-yaml"


def test_validate_file_schema_inference(temp_dir: Path, valid_agent_data: dict[str, Any]) -> None:
    """Test inferring schema from file content."""
    # AgentDefinition has 'metadata' and 'interface'
    valid_agent_data["metadata"]["name"] = "inferred-agent"
    file_path = temp_dir / "agent_inferred.yaml"
    file_path.write_text(yaml.dump(valid_agent_data))

    result = validate_file(file_path)  # No schema provided
    assert result.is_valid
    assert isinstance(result.model, AgentDefinition)

    # RecipeManifest has 'graph' and 'inputs'
    recipe_data = {
        "id": "recipe1",
        "version": "1.0.0",
        "name": "My Recipe",
        "inputs": {},
        "graph": {"nodes": [], "edges": []},
    }
    bec_path = temp_dir / "bec.json"
    bec_path.write_text(json.dumps(recipe_data))

    result_bec = validate_file(bec_path)
    assert result_bec.is_valid
    assert isinstance(result_bec.model, RecipeManifest)


def test_validate_file_inference_more_types(temp_dir: Path) -> None:
    """Test inference for Topology."""
    # Topology (GraphTopology) has 'nodes' and 'edges'
    topo_data: dict[str, Any] = {"nodes": [], "edges": []}
    topo_path = temp_dir / "topo.json"
    topo_path.write_text(json.dumps(topo_data))

    res_topo = validate_file(topo_path)
    assert res_topo.is_valid
    assert isinstance(res_topo.model, Topology)


def test_validate_file_validation_error(temp_dir: Path) -> None:
    """Test validation failure returns structured errors."""
    data = {
        "metadata": {
            "name": "bad-agent"
            # Missing version, id, etc.
        }
    }
    file_path = temp_dir / "invalid.json"
    file_path.write_text(json.dumps(data))

    result = validate_file(file_path, AgentDefinition)
    assert not result.is_valid
    assert result.model is None
    assert len(result.errors) > 0
    # Check structure of error
    err = result.errors[0]
    assert "msg" in err
    assert "loc" in err


def test_validate_file_parse_error(temp_dir: Path) -> None:
    """Test handling of invalid file format."""
    file_path = temp_dir / "broken.json"
    file_path.write_text("{ this is not json }")

    result = validate_file(file_path, AgentDefinition)
    assert not result.is_valid
    assert "Parse error" in str(result.errors)


def test_validate_file_read_error(temp_dir: Path) -> None:
    """Test generic read error."""
    file_path = temp_dir / "error.json"
    file_path.write_text("{}")

    with patch("pathlib.Path.read_text", side_effect=PermissionError("Boom")):
        result = validate_file(file_path, AgentDefinition)
        assert not result.is_valid
        assert "Error reading file" in str(result.errors)
        assert "Boom" in str(result.errors)


def test_validate_file_unknown_schema(temp_dir: Path) -> None:
    """Test failure when schema cannot be inferred."""
    data: dict[str, Any] = {"some": "random data"}
    file_path = temp_dir / "unknown.yaml"
    file_path.write_text(yaml.dump(data))

    result = validate_file(file_path)
    assert not result.is_valid
    assert "Could not infer schema" in str(result.errors)


def test_validate_file_not_found(temp_dir: Path) -> None:
    """Test FileNotFoundError."""
    file_path = temp_dir / "nonexistent.yaml"
    result = validate_file(file_path, AgentDefinition)
    assert not result.is_valid
    assert "File not found" in str(result.errors)


def test_validate_file_not_dict(temp_dir: Path) -> None:
    """Test when file content is not a dict (e.g. list)."""
    file_path = temp_dir / "list.json"
    file_path.write_text("[1, 2, 3]")

    result = validate_file(file_path, AgentDefinition)
    assert not result.is_valid
    assert "must be a dictionary" in str(result.errors)


def test_validate_file_fallback_parsing(temp_dir: Path, valid_agent_data: dict[str, Any]) -> None:
    """Test parsing a file with unknown extension."""
    valid_agent_data["metadata"]["name"] = "txt-agent"

    # Text file with JSON
    file_path_json = temp_dir / "agent.txt"
    file_path_json.write_text(json.dumps(valid_agent_data))

    result = validate_file(file_path_json, AgentDefinition)
    assert result.is_valid

    # Text file with YAML
    file_path_yaml = temp_dir / "agent_y.txt"
    file_path_yaml.write_text(yaml.dump(valid_agent_data))

    result_yaml = validate_file(file_path_yaml, AgentDefinition)
    assert result_yaml.is_valid


def test_validate_file_fallback_parsing_failure(temp_dir: Path) -> None:
    """Test parsing failure for unknown extension."""
    file_path = temp_dir / "garbage.txt"
    # Tabs are forbidden in YAML, and this is not valid JSON
    file_path.write_text("\tkey: value")

    result = validate_file(file_path, AgentDefinition)
    assert not result.is_valid
    assert "Unsupported file extension" in str(result.errors)


def test_validate_file_invalid_schema_arg(temp_dir: Path) -> None:
    """Test invalid schema_type argument."""
    file_path = temp_dir / "agent.json"
    file_path.write_text("{}")

    result = validate_file(file_path, schema_type=123)
    assert not result.is_valid
    assert "Invalid schema_type" in str(result.errors)


def test_validate_file_unknown_alias(temp_dir: Path) -> None:
    """Test unknown string alias."""
    file_path = temp_dir / "agent.json"
    file_path.write_text("{}")

    result = validate_file(file_path, schema_type="unknown_alias")
    assert not result.is_valid
    assert "Unknown schema type alias" in str(result.errors)
