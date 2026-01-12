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
from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.validator import validate_file


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def test_empty_file(temp_dir: Path) -> None:
    """Test validating an empty file."""
    p = temp_dir / "empty.json"
    p.touch()

    result = validate_file(p, AgentManifest)
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
    result = validate_file(p, AgentManifest)
    assert not result.is_valid
    err_str = str(result.errors).lower()
    # It might vary slightly depending on python version, but "recursion" is standard
    assert "recursion" in err_str or "exceeded" in err_str


def test_ambiguous_inference(temp_dir: Path) -> None:
    """Test inference when file matches multiple schemas."""
    # AgentManifest checks 'model_config'. BECManifest checks 'corpus_id'.
    # Create file with both.
    data = {
        "schema_version": "1.0",
        "model_config": "gpt",
        "corpus_id": "corpus",
        # minimal fields for AgentManifest
        "name": "agent",
        "version": "1.0.0",
        "max_cost_limit": 1.0,
        "topology": "t.json",
        # minimal fields for BECManifest
        "cases": [],
    }
    p = temp_dir / "ambiguous.json"
    p.write_text(json.dumps(data))

    # Current implementation checks 'model_config' first (AgentManifest).
    # Since 'extra="forbid"', validation will fail due to presence of 'corpus_id' etc.
    result = validate_file(p)
    assert not result.is_valid
    # Confirm it was validated as AgentManifest by checking for extra field error on 'corpus_id'
    # If it validated as BECManifest, it would complain about 'model_config'.
    err_str = str(result.errors)
    assert "corpus_id" in err_str
    assert "Extra inputs" in err_str or "extra_forbidden" in err_str


def test_unicode_error(temp_dir: Path) -> None:
    """Test file with invalid encoding."""
    p = temp_dir / "bad_encoding.json"
    # Write invalid UTF-8 bytes
    with open(p, "wb") as f:
        f.write(b"\x80\x81")

    result = validate_file(p, AgentManifest)
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
    result = validate_file(p, AgentManifest)
    assert not result.is_valid
    # Should not be a crash
    assert result.errors


def test_validation_generic_exception(temp_dir: Path) -> None:
    """Test generic exception during validation."""
    p = temp_dir / "valid.json"
    p.write_text("{}")

    with patch("coreason_validator.validator.validate_object", side_effect=RuntimeError("Unexpected")):
        result = validate_file(p, AgentManifest)
        assert not result.is_valid
        assert "Validation error: Unexpected" in str(result.errors)
