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


def test_cli_check_json_valid_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a valid file with --json flag.
    """
    f = tmp_path / "agent.yaml"
    f.write_text(
        """
        metadata:
          id: "123e4567-e89b-12d3-a456-426614174000"
          version: "1.0.0"
          name: "test-agent"
          author: "tester"
          created_at: "2025-01-01T00:00:00Z"
        interface:
          inputs: {}
          outputs: {}
        topology:
          steps:
            - id: "s1"
          model_config:
            model: "gpt-4-turbo"
            temperature: 0.7
        dependencies: {}
        integrity_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        """
    )

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is True
    assert output["errors"] == []
    assert "model" in output
    assert output["model"]["metadata"]["name"] == "test-agent"


def test_cli_check_json_invalid_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking an invalid file with --json flag.
    """
    f = tmp_path / "agent_invalid.yaml"
    f.write_text(
        """
        metadata:
          # Missing id
          version: "1.0.0"
          name: "test-agent"
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
        """
    )

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is False
    assert len(output["errors"]) > 0
    # ValidationResult stores model as None if invalid? Let's check ValidationResult definition.
    # is_valid: bool; model: Optional[CoReasonBaseModel] = None
    assert output.get("model") is None


def test_cli_check_json_file_not_found(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a non-existent file with --json flag.
    """
    f = tmp_path / "non_existent.yaml"

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is False
    assert "File not found" in output["errors"][0]["msg"]
