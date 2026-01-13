# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

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


@pytest.fixture
def mock_exporter() -> Generator[MagicMock, None, None]:
    with patch("coreason_validator.cli.export_json_schema") as mock:
        yield mock


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that running with no args or --help prints help."""
    with patch.object(sys, "argv", ["coreason-val", "--help"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
        captured = capsys.readouterr()
        assert "CoReason Validator CLI" in captured.out


def test_cli_no_args(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that running with no args exits with error."""
    with patch.object(sys, "argv", ["coreason-val"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "usage:" in captured.err


def test_check_valid_file(mock_validator: MagicMock, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """Test 'check' subcommand with a valid file."""
    f = tmp_path / "agent.yaml"
    f.touch()

    mock_validator.return_value = ValidationResult(is_valid=True)

    with patch.object(sys, "argv", ["coreason-val", "check", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert "✅ Validation successful" in captured.out
    mock_validator.assert_called_once_with(f)


def test_check_invalid_file(mock_validator: MagicMock, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """Test 'check' subcommand with an invalid file."""
    f = tmp_path / "invalid.yaml"
    f.touch()

    mock_validator.return_value = ValidationResult(
        is_valid=False, errors=[{"msg": "Field missing", "loc": ["root", "field"]}]
    )

    with patch.object(sys, "argv", ["coreason-val", "check", str(f)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Validation failed" in captured.out
    assert "Field missing" in captured.out
    assert "[root -> field]" in captured.out


def test_check_file_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    """Test 'check' subcommand with non-existent file."""
    with patch.object(sys, "argv", ["coreason-val", "check", "non_existent.yaml"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "Error: File not found" in captured.out


def test_export_success(mock_exporter: MagicMock, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """Test 'export' subcommand success."""
    out_dir = tmp_path / "schemas"

    with patch.object(sys, "argv", ["coreason-val", "export", str(out_dir)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert "✅ Schemas exported" in captured.out
    mock_exporter.assert_called_once_with(out_dir)


def test_export_failure(mock_exporter: MagicMock, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """Test 'export' subcommand failure."""
    mock_exporter.side_effect = Exception("Permission denied")

    with patch.object(sys, "argv", ["coreason-val", "export", str(tmp_path)]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert "❌ Export failed: Permission denied" in captured.out
