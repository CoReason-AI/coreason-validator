import json
from pathlib import Path
from typing import Any

import pytest

from coreason_validator.utils.exporter import export_json_schemas


def test_export_json_schemas_creates_files(tmp_path: Path) -> None:
    """
    Test that the exporter creates the expected files in the output directory.
    """
    output_dir = tmp_path / "schemas"
    export_json_schemas(output_dir)

    expected_files = [
        "agent.schema.json",
        "topology.schema.json",
        "bec.schema.json",
        "tool.schema.json",
    ]

    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"{filename} was not created"
        assert file_path.is_file()


def test_export_json_schemas_content_is_valid(tmp_path: Path) -> None:
    """
    Test that the generated files contain valid JSON and look like schemas.
    """
    output_dir = tmp_path / "schemas"
    export_json_schemas(output_dir)

    # Check agent.schema.json as a sample
    agent_schema_path = output_dir / "agent.schema.json"
    content = json.loads(agent_schema_path.read_text(encoding="utf-8"))

    assert "properties" in content
    assert "title" in content
    assert content["title"] == "AgentManifest"

    # Check specific field existence
    assert "schema_version" in content["properties"]
    assert "model_config" in content["properties"]


def test_export_json_schemas_overwrites_existing(tmp_path: Path) -> None:
    """
    Test that the exporter overwrites existing files.
    """
    output_dir = tmp_path / "schemas"
    output_dir.mkdir()

    agent_schema_path = output_dir / "agent.schema.json"
    agent_schema_path.write_text("old content", encoding="utf-8")

    export_json_schemas(output_dir)

    content = json.loads(agent_schema_path.read_text(encoding="utf-8"))
    assert content["title"] == "AgentManifest"


def test_export_json_schemas_handles_write_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
        export_json_schemas(output_dir)
