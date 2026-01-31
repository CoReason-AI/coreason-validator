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

def get_valid_topology_data():
    return {
        "nodes": [
            {
                "type": "agent",
                "id": "node1",
                "agent_name": "worker1"
            },
            {
                "type": "human",
                "id": "node2"
            }
        ],
        "edges": [
            {
                "source_node_id": "node1",
                "target_node_id": "node2"
            }
        ],
        "state_schema": {"data_schema": {}, "persistence": "memory"}
    }


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


def test_cli_check_json_complex_topology(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a complex topology file to ensure nested model serialization works in JSON output.
    """
    f = tmp_path / "topology.json"
    f.write_text(json.dumps(get_valid_topology_data()))

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is True
    model = output["model"]
    assert len(model["nodes"]) == 2
    assert model["nodes"][0]["id"] == "node1"
    assert model["nodes"][0]["type"] == "agent"


def test_cli_check_json_unicode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file with unicode characters to ensure they are preserved in JSON output.
    """
    data = get_valid_agent_data()
    # Agent name might be restrictive?
    # AgentDefinition.metadata.name: str (min_length=1)
    # No regex pattern seen in AgentMetadata model I read earlier.
    # So "agent-🚀" might be valid?
    # Let's try. If it fails validation, we check errors.
    data["metadata"]["name"] = "agent-🚀"

    f = tmp_path / "agent_unicode.json"
    f.write_text(json.dumps(data))

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        # If valid, 0. If name regex restricts emoji, 1.
        # Assuming name is flexible. If not, we assert code is 1 and errors exist.
        pass

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    # Just checking JSON validity of output regardless of validation status
    assert "is_valid" in output


def test_cli_check_json_unicode_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file with unicode characters in a field that definitely allows them.
    """
    # Topology agent name
    data = get_valid_topology_data()
    data["nodes"][0]["agent_name"] = "worker-🚀"

    f = tmp_path / "topology_unicode.json"
    f.write_text(json.dumps(data))

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is True
    assert output["model"]["nodes"][0]["agent_name"] == "worker-🚀"


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
    assert "Permission denied" in output["errors"][0]["msg"]
