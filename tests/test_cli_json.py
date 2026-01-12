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
        schema_version: "1.0"
        name: "test-agent"
        version: "1.0.0"
        model_config: "gpt-4-turbo"
        max_cost_limit: 10.0
        topology: "topology.yaml"
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
    assert output["model"]["name"] == "test-agent"


def test_cli_check_json_invalid_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking an invalid file with --json flag.
    """
    f = tmp_path / "agent_invalid.yaml"
    f.write_text(
        """
        schema_version: "1.0"
        name: "test-agent"
        # Missing version
        model_config: "gpt-4-turbo"
        max_cost_limit: 10.0
        topology: "topology.yaml"
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
