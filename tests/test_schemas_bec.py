from unittest.mock import patch

import pytest
from pydantic import ValidationError

from coreason_validator.schemas.bec import BECManifest, TestCase


def test_bec_manifest_valid() -> None:
    """
    Test a valid BECManifest with valid JSON schema in expected_output_structure.
    """
    valid_schema = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    }

    cases = [
        TestCase(
            id="test-1",
            prompt="Summarize this.",
            context_files=["data.txt"],
            expected_output_structure=valid_schema,
        )
    ]

    manifest = BECManifest(corpus_id="corpus-001", cases=cases)

    assert manifest.corpus_id == "corpus-001"
    assert manifest.cases[0].id == "test-1"
    assert manifest.cases[0].expected_output_structure == valid_schema
    assert manifest.schema_version == "1.0"


def test_bec_manifest_invalid_json_schema() -> None:
    """
    Test that an invalid JSON schema raises a ValidationError.
    """
    invalid_schema = {
        "type": "object",
        "properties": {"summary": {"type": "unknown_type"}},  # 'unknown_type' is not valid
    }

    with pytest.raises(ValidationError) as excinfo:
        TestCase(
            id="test-2",
            prompt="Fail me.",
            expected_output_structure=invalid_schema,
        )

    assert "Invalid JSON Schema" in str(excinfo.value)


def test_bec_manifest_optional_structure() -> None:
    """
    Test that expected_output_structure is optional.
    """
    case = TestCase(
        id="test-3",
        prompt="No schema needed.",
    )
    assert case.expected_output_structure is None

    manifest = BECManifest(corpus_id="corpus-002", cases=[case])
    assert len(manifest.cases) == 1


def test_bec_manifest_hashing() -> None:
    """
    Test canonical hashing for BECManifest.
    """
    schema = {"type": "string"}
    case1 = TestCase(id="t1", prompt="p1", expected_output_structure=schema)
    manifest1 = BECManifest(corpus_id="c1", cases=[case1])

    # Whitespace difference in schema shouldn't affect validation but might affect hash
    # IF the hash logic didn't normalize JSON.
    # But CoReasonBaseModel.canonical_hash normalizes it.

    # Let's verify deterministic hash
    hash1 = manifest1.canonical_hash()

    case2 = TestCase(id="t1", prompt="p1", expected_output_structure=schema)
    manifest2 = BECManifest(corpus_id="c1", cases=[case2])

    assert hash1 == manifest2.canonical_hash()


def test_bec_manifest_empty_cases() -> None:
    """
    Test that cases list cannot be empty.
    """
    with pytest.raises(ValidationError):
        BECManifest(corpus_id="c1", cases=[])


def test_bec_manifest_unexpected_validation_error() -> None:
    """
    Test that an unexpected exception during validation raises ValueError.
    """
    valid_schema = {"type": "string"}

    # We patch validator_for to raise a generic Exception
    with patch("coreason_validator.schemas.bec.validator_for", side_effect=Exception("Unexpected boom")):
        with pytest.raises(ValidationError) as excinfo:
            TestCase(
                id="test-unexpected",
                prompt="Boom",
                expected_output_structure=valid_schema,
            )

    # Check that the error message contains our expected string
    assert "Invalid JSON Schema: Unexpected boom" in str(excinfo.value)
