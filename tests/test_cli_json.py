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
from datetime import datetime

import pytest

from coreason_validator.cli import main

VALID_HASH = "a" * 64
VALID_UUID = "123e4567-e89b-12d3-a456-426614174000"

def get_valid_agent_data():
    return {
        "metadata": {
            "id": VALID_UUID,
            "version": "1.0.0",
            "name": "test-agent",
            "author": "tester",
            "created_at": datetime.utcnow().isoformat(),
        },
        "interface": {
            "inputs": {"type": "object"},
            "outputs": {"type": "object"},
        },
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "node1",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {},
        "integrity_hash": VALID_HASH,
    }


def test_cli_check_json_valid_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a valid file with --json flag.
    """
    f = tmp_path / "agent.json"
    f.write_text(json.dumps(get_valid_agent_data()))

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
    data = get_valid_agent_data()
    # Invalidate it by removing required field
    del data["metadata"]["name"]

    f = tmp_path / "agent_invalid.json"
    f.write_text(json.dumps(data))

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is False
    assert len(output["errors"]) > 0
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
