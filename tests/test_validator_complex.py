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
from coreason_manifest.definitions.agent import AgentDefinition

from coreason_validator.validator import validate_file

VALID_HASH = "a" * 64
VALID_UUID = "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def test_empty_file(temp_dir: Path) -> None:
    """Test validating an empty file."""
    p = temp_dir / "empty.json"
    p.touch()

    result = validate_file(p, AgentDefinition)
    assert not result.is_valid
    # Expect JSONDecodeError (Parse error)
    # json.loads("") raises JSONDecodeError
    assert "Parse error" in str(result.errors)


def test_yaml_cycle_recursion(temp_dir: Path) -> None:
    """Test YAML file with cyclic reference."""
    p = temp_dir / "cycle.yaml"
    # YAML cycle: &a { key: *a } creates a dict containing itself
    p.write_text("&a { key: *a }")

    # yaml.safe_load loads this. sanitize_inputs will recurse.
    # It should hit recursion limit and raise RecursionError.
    # validate_file should catch Exception and report it.
    result = validate_file(p, AgentDefinition)
    assert not result.is_valid
    err_str = str(result.errors).lower()
    # It might vary slightly depending on python version, but "recursion" is standard
    assert "recursion" in err_str or "exceeded" in err_str


def test_ambiguous_inference(temp_dir: Path) -> None:
    """Test inference when file matches multiple schemas."""
    # Agent checks: integrity_hash, config
    # Recipe checks: topology, interface
    # Create file with all of them.
    data = {
        # Agent keys
        "integrity_hash": VALID_HASH,
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "node1",
            "model_config": {"model": "m", "temperature": 0.0},
        },
        # Recipe keys
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"nodes": [], "edges": [], "state_schema": {"data_schema": {}, "persistence": "memory"}},
        # Missing other required fields for Agent (metadata) or Recipe (id, version, state, parameters)
        # to ensure we fail validation, but we want to know WHICH schema it picked.
        "extra_field_for_agent": "should fail if agent",
    }
    p = temp_dir / "ambiguous.json"
    p.write_text(json.dumps(data))

    # Current registry order puts 'agent' before 'recipe'.
    # So it should infer AgentDefinition.
    # AgentDefinition has extra="forbid".
    # It should fail because of 'interface' (extra), 'topology'
    # (Wait, AgentDefinition DOES NOT have 'topology' in new schema?
    # It has 'config' which contains 'nodes'/'edges').
    # AgentDefinition has 'interface' too!
    # AgentDefinition structure: metadata, interface, config, dependencies, policy, observability, integrity_hash.

    # So if it infers AgentDefinition:
    # 'topology' is extra.
    # 'extra_field_for_agent' is extra.

    result = validate_file(p)
    assert not result.is_valid

    # We want to confirm it tried AgentDefinition.
    # If it tried RecipeManifest, it would complain about 'config', 'integrity_hash', 'extra_field_for_agent'.
    # Both sets of extra fields are present.
    # But we can assume the registry order.

    err_str = str(result.errors)
    assert "extra_field_for_agent" in err_str or "Extra inputs" in err_str or "extra_forbidden" in err_str


def test_unicode_error(temp_dir: Path) -> None:
    """Test file with invalid encoding."""
    p = temp_dir / "bad_encoding.json"
    # Write invalid UTF-8 bytes
    with open(p, "wb") as f:
        f.write(b"\x80\x81")

    result = validate_file(p, AgentDefinition)
    assert not result.is_valid
    assert "Error reading file" in str(result.errors)
    err_str = str(result.errors).lower()
    assert "codec" in err_str or "utf-8" in err_str


def test_deeply_nested(temp_dir: Path) -> None:
    """Test deeply nested structure."""
    depth = 200
    data = "leaf"
    for _ in range(depth):
        data = {"next": data}  # type: ignore

    p = temp_dir / "deep.json"
    p.write_text(json.dumps(data))

    # This might fail schema validation (extra fields) but shouldn't crash
    result = validate_file(p, AgentDefinition)
    assert not result.is_valid
    # Should not be a crash
    assert result.errors


def test_validation_generic_exception(temp_dir: Path) -> None:
    """Test generic exception during validation."""
    p = temp_dir / "valid.json"
    p.write_text("{}")

    with patch("coreason_validator.validator.validate_object", side_effect=RuntimeError("Unexpected")):
        result = validate_file(p, AgentDefinition)
        assert not result.is_valid
        assert "Validation error: Unexpected" in str(result.errors)
