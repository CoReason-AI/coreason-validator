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
from pathlib import Path
from typing import Any

import pytest
from coreason_manifest.definitions.agent import AgentDefinition

from coreason_validator.utils.exporter import export_json_schema, generate_validation_report
from coreason_validator.validator import ValidationResult


def test_export_json_schema_creates_files(tmp_path: Path) -> None:
    """
    Test that the exporter creates the expected files in the output directory.
    """
    output_dir = tmp_path / "schemas"
    export_json_schema(output_dir)

    expected_files = [
        "agent.schema.json",
        "topology.schema.json",
        "bec.schema.json",
    ]

    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"{filename} was not created"
        assert file_path.is_file()


def test_export_json_schema_content_is_valid(tmp_path: Path) -> None:
    """
    Test that the generated files contain valid JSON and look like schemas.
    """
    output_dir = tmp_path / "schemas"
    export_json_schema(output_dir)

    # Check agent.schema.json as a sample
    agent_schema_path = output_dir / "agent.schema.json"
    content = json.loads(agent_schema_path.read_text(encoding="utf-8"))

    assert "properties" in content
    assert "title" in content
    assert content["title"] == "CoReason Agent Manifest"

    # Check specific field existence
    assert "metadata" in content["properties"]
    assert "interface" in content["properties"]


def test_export_json_schema_overwrites_existing(tmp_path: Path) -> None:
    """
    Test that the exporter overwrites existing files.
    """
    output_dir = tmp_path / "schemas"
    output_dir.mkdir()

    agent_schema_path = output_dir / "agent.schema.json"
    agent_schema_path.write_text("old content", encoding="utf-8")

    export_json_schema(output_dir)

    content = json.loads(agent_schema_path.read_text(encoding="utf-8"))
    assert "properties" in content


def test_export_json_schema_handles_write_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test handling of write errors during export.
    """
    output_dir = tmp_path / "schemas"
    output_dir.mkdir()

    # Mock open to raise PermissionError
    # We use a context manager mock since 'open' is used as a context manager
    def mock_open(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError("Access denied")

    monkeypatch.setattr("builtins.open", mock_open)

    with pytest.raises(PermissionError):
        export_json_schema(output_dir)


def test_export_verifies_nested_definitions(tmp_path: Path) -> None:
    """
    Test that the exported schema for Topology includes nested definitions.
    """
    output_dir = tmp_path / "schemas"
    export_json_schema(output_dir)

    topology_path = output_dir / "topology.schema.json"
    content = json.loads(topology_path.read_text(encoding="utf-8"))

    # Pydantic V2 uses $defs for nested model definitions
    assert "$defs" in content, "Schema missing $defs for nested models"
    # Topology uses Node (union) and Edge
    assert "Node" in content["$defs"] or "AgentNode" in content["$defs"]


def test_export_fails_if_output_is_file(tmp_path: Path) -> None:
    """
    Test failure when the output path is an existing file, preventing directory creation.
    """
    output_file = tmp_path / "is_a_file"
    output_file.touch()

    # Should raise NotADirectoryError or FileExistsError (OS dependent)
    # mkdir(parents=True) raises FileExistsError if existing path is a file
    with pytest.raises((FileExistsError, NotADirectoryError)):
        export_json_schema(output_file)


def test_export_failure_in_model_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test error handling when the model schema generation itself fails.
    """
    output_dir = tmp_path / "schemas"

    # Mock AgentDefinition.model_json_schema to raise an error
    def mock_schema_gen(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("Simulated schema generation failure")

    monkeypatch.setattr(AgentDefinition, "model_json_schema", mock_schema_gen)

    with pytest.raises(ValueError, match="Simulated schema generation failure"):
        export_json_schema(output_dir)


def test_generate_validation_report() -> None:
    result = ValidationResult(is_valid=True, errors=[], validation_metadata={"validated_by": "me"})
    report = generate_validation_report(result)
    assert report["is_valid"] is True
    assert report["validation_metadata"]["validated_by"] == "me"
