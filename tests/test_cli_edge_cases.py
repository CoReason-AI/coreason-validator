import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from coreason_validator.cli import main
from coreason_validator.validator import ValidationResult


@pytest.fixture
def mock_validator() -> Generator[MagicMock, None, None]:
    with patch("coreason_validator.cli.validate_file") as mock:
        yield mock


def test_check_directory_instead_of_file(
    mock_validator: MagicMock, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Test 'check' subcommand when path is a directory."""
    # Setup: Create a directory
    d = tmp_path / "subdir"
    d.mkdir()

    # Mock validator to fail or behave as if it read a dir (depending on implementation)
    # Actually, validate_file does path.read_text(), which raises IsADirectoryError.
    # The CLI calls validate_file inside a try/except block?
    # Let's look at validate_file implementation. It catches Exception.

    # We need to simulate validate_file returning an error because of IsADirectoryError
    mock_validator.return_value = ValidationResult(
        is_valid=False, errors=[{"msg": "Error reading file: Is a directory"}]
    )

    with patch.object(sys, "argv", ["coreason-val", "check", str(d)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Validation failed" in captured.out
    assert "Is a directory" in captured.out


def test_check_unicode_filename(mock_validator: MagicMock, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """Test 'check' with a complex unicode filename."""
    # 🐍_config.yaml
    f = tmp_path / "🐍_config.yaml"
    f.touch()

    mock_validator.return_value = ValidationResult(is_valid=True)

    with patch.object(sys, "argv", ["coreason-val", "check", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert f"✅ Validation successful: {f}" in captured.out
    mock_validator.assert_called_once_with(f)


def test_check_deeply_nested_error(
    mock_validator: MagicMock, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Test 'check' output formatting for deep nesting."""
    f = tmp_path / "deep.yaml"
    f.touch()

    # Simulate a deep error location: root -> level1 -> level2 -> field
    mock_validator.return_value = ValidationResult(
        is_valid=False, errors=[{"msg": "Invalid value", "loc": ["root", "level1", "level2", "field"]}]
    )

    with patch.object(sys, "argv", ["coreason-val", "check", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    # Check for the formatted arrow string
    assert "[root -> level1 -> level2 -> field]: Invalid value" in captured.out


def test_export_target_is_file(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """Test 'export' when the target is an existing file, not a directory."""
    # Create a file
    f = tmp_path / "im_a_file.txt"
    f.touch()

    # exporter.export_json_schemas calls output_dir.mkdir(parents=True, exist_ok=True)
    # if output_dir is a file, mkdir raises FileExistsError (or NotADirectoryError depending on OS/path)

    with patch.object(sys, "argv", ["coreason-val", "export", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Export failed" in captured.out
