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
from unittest.mock import patch

import pytest

from coreason_validator.cli import main


def test_cli_check_json_malformed_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file with syntax errors (malformed YAML) with --json flag.
    """
    f = tmp_path / "malformed.yaml"
    f.write_text(":")

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is False
    assert len(output["errors"]) == 1
    msg = output["errors"][0]["msg"]
    assert "Parse error" in msg or "File content must be a dictionary" in msg or "Could not infer" in msg


def test_cli_check_json_complex_topology(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a complex topology file to ensure nested model serialization works in JSON output.
    """
    f = tmp_path / "topology.yaml"
    f.write_text(
        """
        nodes:
          - id: "start"
            type: "agent"
            agent_name: "calculator"
          - id: "end"
            type: "human"
            timeout_seconds: 60
        edges:
          - source_node_id: "start"
            target_node_id: "end"
        """
    )

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is True
    model = output["model"]
    assert len(model["nodes"]) == 2
    assert model["nodes"][0]["id"] == "start"
    assert model["nodes"][0]["agent_name"] == "calculator"


def test_cli_check_json_unicode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file with unicode characters to ensure they are preserved in JSON output.
    """
    f = tmp_path / "agent_unicode.yaml"
    f.write_text(
        """
        metadata:
          id: "123e4567-e89b-12d3-a456-426614174000"
          version: "1.0.0"
          name: "agent-🚀"
          author: "tester"
          created_at: "2025-01-01T00:00:00Z"
        interface:
          inputs: {}
          outputs: {}
        topology:
          steps: []
          model_config:
            model: "gpt-4-turbo"
            temperature: 0.7
        dependencies: {}
        integrity_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        """,
        encoding="utf-8",
    )

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        # Expect success because new schema allows unicode in name
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is True
    assert output["model"]["metadata"]["name"] == "agent-🚀"


def test_cli_check_json_unicode_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file with unicode characters in a field that allows them.
    """
    f = tmp_path / "topology_unicode.yaml"
    f.write_text(
        """
        nodes:
          - id: "start"
            type: "agent"
            agent_name: "calculator 🌍"
        edges: []
        """,
        encoding="utf-8",
    )

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is True
    # Check that the emoji is present in the output model
    assert output["model"]["nodes"][0]["agent_name"] == "calculator 🌍"


def test_cli_check_json_read_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file that cannot be read (PermissionError).
    """
    f = tmp_path / "locked.yaml"
    f.touch()

    # Mock Path.read_text to raise PermissionError
    with patch.object(Path, "read_text", side_effect=PermissionError("Permission denied")):
        with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 1

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is False
    assert "Error reading file" in output["errors"][0]["msg"]
