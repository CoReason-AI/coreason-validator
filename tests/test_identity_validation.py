from pathlib import Path

from coreason_identity.models import UserContext

from coreason_validator.validator import validate_file


def test_validation_with_user_context(tmp_path: Path) -> None:
    # Create a valid tool call file (Kernel schema: ToolCallRequestPart)
    p = tmp_path / "tool.json"
    p.write_text('{"type": "tool_call", "name": "my_tool", "arguments": {"x": 1}}')

    ctx = UserContext(user_id="auth0|123", email="test@coreason.ai", groups=["admin"])

    # We need to specify schema_type because inference might fail or pick something else if ambiguous,
    # but 'tool' is explicit.
    result = validate_file(p, schema_type="tool", user_context=ctx)

    assert result.is_valid, f"Errors: {result.errors}"
    assert result.validation_metadata["validated_by"] == "auth0|123 (test@coreason.ai)"
    assert result.validation_metadata["signature_context"] == "Authenticated via CoReason Identity"
    assert result.validation_metadata["validation_status"] == "PASS"
    assert "timestamp" in result.validation_metadata


def test_validation_without_user_context(tmp_path: Path) -> None:
    p = tmp_path / "tool.json"
    p.write_text('{"type": "tool_call", "name": "my_tool", "arguments": {"x": 1}}')

    result = validate_file(p, schema_type="tool", user_context=None)

    assert result.is_valid, f"Errors: {result.errors}"
    assert result.validation_metadata["validated_by"] == "SYSTEM_AUTOMATION"
    assert result.validation_metadata["signature_context"] == "Unattributed"
