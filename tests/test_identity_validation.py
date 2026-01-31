import json
from pathlib import Path

from coreason_identity.models import UserContext

from coreason_validator.validator import validate_file


def test_validation_with_user_context(tmp_path: Path) -> None:
    # Create a valid Agent file (ToolCall is removed)
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "test-agent",
            "author": "tester",
            "created_at": "2025-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"steps": [{"id": "s1"}], "model_config": {"model": "gpt-4", "temperature": 0.7}},
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }
    p = tmp_path / "agent.json"
    p.write_text(json.dumps(data))

    ctx = UserContext(user_id="auth0|123", email="test@coreason.ai", groups=["admin"])

    result = validate_file(p, schema_type="agent", user_context=ctx)

    assert result.is_valid, f"Errors: {result.errors}"
    assert result.validation_metadata["validated_by"] == "auth0|123 (test@coreason.ai)"
    assert result.validation_metadata["signature_context"] == "Authenticated via CoReason Identity"
    assert result.validation_metadata["validation_status"] == "PASS"
    assert "timestamp" in result.validation_metadata


def test_validation_without_user_context(tmp_path: Path) -> None:
    # Create a valid Agent file
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "test-agent",
            "author": "tester",
            "created_at": "2025-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"steps": [{"id": "s1"}], "model_config": {"model": "gpt-4", "temperature": 0.7}},
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }
    p = tmp_path / "agent.json"
    p.write_text(json.dumps(data))

    result = validate_file(p, schema_type="agent", user_context=None)

    assert result.is_valid, f"Errors: {result.errors}"
    assert result.validation_metadata["validated_by"] == "SYSTEM_AUTOMATION"
    assert result.validation_metadata["signature_context"] == "Unattributed"
