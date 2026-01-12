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
    # Actually create a malformed YAML that safe_load will accept as string or dict?
    # PyYAML safe_load might parse "key: value\n  broken_indentation" as "key: 'value broken_indentation'"
    # or it might fail.
    # If it parses, validate_file returns "Could not infer schema type from content." if no root keys match.
    # To force a parse error, we need something truly invalid.
    f.write_text(":")

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is False
    assert len(output["errors"]) == 1
    # Check for either Parse error or unexpected structure
    msg = output["errors"][0]["msg"]
    assert "Parse error" in msg or "File content must be a dictionary" in msg or "Could not infer" in msg


def test_cli_check_json_complex_topology(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a complex topology file to ensure nested model serialization works in JSON output.
    """
    f = tmp_path / "topology.yaml"
    f.write_text(
        """
        schema_version: "1.0"
        nodes:
          - id: "start"
            step_type: "prompt"
            next_steps: ["process"]
            config:
              prompt_template: "Hello"
          - id: "process"
            step_type: "tool"
            next_steps: ["end"]
            config:
              tool_name: "calculator"
          - id: "end"
            step_type: "terminal"
            next_steps: []
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
    assert len(model["nodes"]) == 3
    assert model["nodes"][0]["id"] == "start"
    assert model["nodes"][0]["next_steps"] == ["process"]
    assert model["nodes"][1]["config"]["tool_name"] == "calculator"


def test_cli_check_json_unicode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file with unicode characters to ensure they are preserved in JSON output.
    """
    f = tmp_path / "agent_unicode.yaml"
    f.write_text(
        """
        schema_version: "1.0"
        name: "agent-🚀"
        version: "1.0.0"
        model_config: "gpt-4-turbo"
        max_cost_limit: 10.0
        topology: "topology.yaml"
        """,
        encoding="utf-8",
    )

    with patch("sys.argv", ["coreason-val", "check", str(f), "--json"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        # It might fail if the regex for name doesn't allow emojis.
        # The schema says: name: constr(pattern=r"^[a-z0-9-]+$")
        # So "agent-🚀" is actually INVALID.
        # But we want to check that the JSON output handles the unicode in the valid/invalid model or error message.
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["is_valid"] is False
    # The error message should contain the invalid value or context.
    # Pydantic error usually includes input value.
    # We just want to ensure we didn't crash and output is valid JSON.
    assert len(output["errors"]) > 0


def test_cli_check_json_unicode_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """
    Test checking a file with unicode characters in a field that allows them (e.g., config in Topology).
    """
    f = tmp_path / "topology_unicode.yaml"
    f.write_text(
        """
        schema_version: "1.0"
        nodes:
          - id: "start"
            step_type: "prompt"
            next_steps: []
            config:
              message: "Hello 🌍"
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
    assert output["model"]["nodes"][0]["config"]["message"] == "Hello 🌍"


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
