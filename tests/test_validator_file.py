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
from typing import Iterator
from unittest.mock import patch

import pytest
import yaml

from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.schemas.bec import BECManifest
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.schemas.topology import TopologyGraph
from coreason_validator.validator import validate_file


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def test_validate_file_json_success(temp_dir: Path) -> None:
    """Test validating a valid JSON file."""
    data = {
        "schema_version": "1.0",
        "name": "test-agent",
        "version": "1.0.0",
        "model_config": "gpt-4",
        "max_cost_limit": 10.0,
    }
    file_path = temp_dir / "agent.json"
    file_path.write_text(json.dumps(data))

    result = validate_file(file_path, AgentManifest)
    assert result.is_valid
    assert result.model is not None
    assert isinstance(result.model, AgentManifest)
    assert result.model.name == "test-agent"
    assert not result.errors


def test_validate_file_yaml_success(temp_dir: Path) -> None:
    """Test validating a valid YAML file."""
    data = {
        "schema_version": "1.0",
        "name": "test-agent-yaml",
        "version": "1.0.0",
        "model_config": "gpt-4",
        "max_cost_limit": 5.0,
    }
    file_path = temp_dir / "agent.yaml"
    file_path.write_text(yaml.dump(data))

    result = validate_file(file_path, AgentManifest)
    assert result.is_valid
    assert isinstance(result.model, AgentManifest)
    assert result.model.name == "test-agent-yaml"


def test_validate_file_schema_inference(temp_dir: Path) -> None:
    """Test inferring schema from file content."""
    # AgentManifest has 'model_config'
    agent_data = {
        "schema_version": "1.0",
        "name": "inferred-agent",
        "version": "1.0.0",
        "model_config": "gpt-4",
        "max_cost_limit": 10.0,
    }
    file_path = temp_dir / "agent_inferred.yaml"
    file_path.write_text(yaml.dump(agent_data))

    result = validate_file(file_path)  # No schema provided
    assert result.is_valid
    assert isinstance(result.model, AgentManifest)

    # BECManifest has 'corpus_id'
    bec_data = {
        "schema_version": "1.0",
        "corpus_id": "test-corpus",
        "cases": [{"id": "1", "prompt": "hi", "expected_output_structure": {"type": "object"}}],
    }
    bec_path = temp_dir / "bec.json"
    bec_path.write_text(json.dumps(bec_data))

    result_bec = validate_file(bec_path)
    assert result_bec.is_valid
    assert isinstance(result_bec.model, BECManifest)


def test_validate_file_inference_more_types(temp_dir: Path) -> None:
    """Test inference for Topology and ToolCall."""
    # Topology
    topo_data = {"schema_version": "1.0", "nodes": [{"id": "n1", "step_type": "prompt"}]}
    topo_path = temp_dir / "topo.json"
    topo_path.write_text(json.dumps(topo_data))

    res_topo = validate_file(topo_path)
    assert res_topo.is_valid
    assert isinstance(res_topo.model, TopologyGraph)

    # ToolCall
    tool_data = {"tool_name": "search", "arguments": {"q": "foo"}}
    tool_path = temp_dir / "tool.json"
    tool_path.write_text(json.dumps(tool_data))

    res_tool = validate_file(tool_path)
    assert res_tool.is_valid
    assert isinstance(res_tool.model, ToolCall)


def test_validate_file_validation_error(temp_dir: Path) -> None:
    """Test validation failure returns structured errors."""
    data = {
        "schema_version": "1.0",
        "name": "bad-agent",
        # Missing version, model_config, etc.
    }
    file_path = temp_dir / "invalid.json"
    file_path.write_text(json.dumps(data))

    result = validate_file(file_path, AgentManifest)
    assert not result.is_valid
    assert result.model is None
    assert len(result.errors) > 0
    # Check structure of error
    err = result.errors[0]
    assert "msg" in err


def test_validate_file_parse_error(temp_dir: Path) -> None:
    """Test handling of invalid file format."""
    file_path = temp_dir / "broken.json"
    file_path.write_text("{ this is not json }")

    result = validate_file(file_path, AgentManifest)
    assert not result.is_valid
    assert "Parse error" in str(result.errors)


def test_validate_file_read_error(temp_dir: Path) -> None:
    """Test generic read error."""
    file_path = temp_dir / "error.json"
    file_path.write_text("{}")

    with patch("pathlib.Path.read_text", side_effect=PermissionError("Boom")):
        result = validate_file(file_path, AgentManifest)
        assert not result.is_valid
        assert "Error reading file" in str(result.errors)
        assert "Boom" in str(result.errors)


def test_validate_file_unknown_schema(temp_dir: Path) -> None:
    """Test failure when schema cannot be inferred."""
    data = {"some": "random data"}
    file_path = temp_dir / "unknown.yaml"
    file_path.write_text(yaml.dump(data))

    result = validate_file(file_path)
    assert not result.is_valid
    assert "Could not infer schema" in str(result.errors)


def test_validate_file_not_found(temp_dir: Path) -> None:
    """Test FileNotFoundError."""
    file_path = temp_dir / "nonexistent.yaml"
    result = validate_file(file_path, AgentManifest)
    assert not result.is_valid
    assert "File not found" in str(result.errors)


def test_validate_file_not_dict(temp_dir: Path) -> None:
    """Test when file content is not a dict (e.g. list)."""
    file_path = temp_dir / "list.json"
    file_path.write_text("[1, 2, 3]")

    result = validate_file(file_path, AgentManifest)
    assert not result.is_valid
    assert "must be a dictionary" in str(result.errors)


def test_validate_file_fallback_parsing(temp_dir: Path) -> None:
    """Test parsing a file with unknown extension."""
    data = {
        "schema_version": "1.0",
        "name": "txt-agent",
        "version": "1.0.0",
        "model_config": "gpt",
        "max_cost_limit": 1.0,
    }

    # Text file with JSON
    file_path_json = temp_dir / "agent.txt"
    file_path_json.write_text(json.dumps(data))

    result = validate_file(file_path_json, AgentManifest)
    assert result.is_valid

    # Text file with YAML
    file_path_yaml = temp_dir / "agent_y.txt"
    file_path_yaml.write_text(yaml.dump(data))

    result_yaml = validate_file(file_path_yaml, AgentManifest)
    assert result_yaml.is_valid


def test_validate_file_fallback_parsing_failure(temp_dir: Path) -> None:
    """Test parsing failure for unknown extension."""
    file_path = temp_dir / "garbage.txt"
    # Tabs are forbidden in YAML, and this is not valid JSON
    file_path.write_text("\tkey: value")

    result = validate_file(file_path, AgentManifest)
    assert not result.is_valid
    assert "Unsupported file extension" in str(result.errors)


def test_validate_file_invalid_schema_arg(temp_dir: Path) -> None:
    """Test invalid schema_type argument."""
    file_path = temp_dir / "agent.json"
    file_path.write_text("{}")

    result = validate_file(file_path, schema_type=123)  # type: ignore
    assert not result.is_valid
    assert "Invalid schema_type" in str(result.errors)


def test_validate_file_unknown_alias(temp_dir: Path) -> None:
    """Test unknown string alias."""
    file_path = temp_dir / "agent.json"
    file_path.write_text("{}")

    result = validate_file(file_path, schema_type="unknown_alias")
    assert not result.is_valid
    assert "Unknown schema type alias" in str(result.errors)
