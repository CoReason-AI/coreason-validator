# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import pytest
from pydantic import ValidationError

from coreason_validator.schemas.bec import BECManifest, BECTestCase


def test_bectestcase_hash_stability() -> None:
    """
    Edge Case: Ensure that the class rename (TestCase -> BECTestCase) does not alter the canonical hash.
    The hash must be derived SOLELY from the data fields, not the class name.
    """
    # 1. Create a BECTestCase instance
    case = BECTestCase(
        id="stability-test",
        prompt="Calculate hash.",
        context_files=["a.txt", "b.txt"],
        expected_output_structure={"type": "object"},
    )

    # 2. Compute its hash
    model_hash = case.canonical_hash()

    # 3. Manually simulate what the hash SHOULD be (raw dict -> json dump -> sha256)
    # This mirrors the logic in CoReasonBaseModel.canonical_hash
    import hashlib
    import json

    data = {
        "id": "stability-test",
        "prompt": "Calculate hash.",
        "context_files": ["a.txt", "b.txt"],
        "expected_output_structure": {"type": "object"},
    }

    # Sort keys, no spaces
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    expected_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    assert model_hash == expected_hash, "Hash should depend only on data content"


def test_bectestcase_advanced_json_schema() -> None:
    """
    Complex Scenario: Verify that BECTestCase accepts advanced JSON Schema features
    like definitions, $ref, and conditional logic.
    """
    advanced_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "definitions": {
            "address": {
                "type": "object",
                "properties": {"street": {"type": "string"}, "city": {"type": "string"}},
                "required": ["street", "city"],
            }
        },
        "properties": {
            "billing_address": {"$ref": "#/definitions/address"},
            "shipping_address": {"$ref": "#/definitions/address"},
        },
        "if": {"properties": {"country": {"const": "US"}}},
        "then": {"properties": {"postal_code": {"pattern": "\\d{5}"}}},
    }

    case = BECTestCase(id="complex-schema-1", prompt="Generate user data", expected_output_structure=advanced_schema)

    assert case.expected_output_structure == advanced_schema


def test_bectestcase_invalid_ref_schema() -> None:
    """
    Edge Case: A JSON Schema with a syntactically invalid $ref usage
    (though strict resolution might depend on external tools, jsonschema.check_schema
    validates the structure of the ref).
    """
    # Note: jsonschema.validators.check_schema usually checks the meta-schema validity.
    # It might NOT catch a dangling reference (e.g., "#/definitions/missing")
    # unless we actually try to VALIDATE an instance against it.
    # However, it SHOULD catch invalid TYPES for $ref (e.g. $ref must be a string).

    invalid_schema = {
        "type": "object",
        "properties": {
            "bad_ref": {"$ref": 123}  # Invalid: $ref must be a string
        },
    }

    with pytest.raises(ValidationError) as excinfo:
        BECTestCase(id="bad-ref-test", prompt="Fail me", expected_output_structure=invalid_schema)

    assert "Invalid JSON Schema" in str(excinfo.value)


def test_bectestcase_recursion_in_schema() -> None:
    """
    Complex Scenario: Recursive schema definition (e.g., a tree structure).
    """
    recursive_schema = {
        "definitions": {
            "node": {
                "type": "object",
                "properties": {
                    "value": {"type": "integer"},
                    "children": {"type": "array", "items": {"$ref": "#/definitions/node"}},
                },
            }
        },
        "$ref": "#/definitions/node",
    }

    case = BECTestCase(id="recursive-tree", prompt="Generate a tree", expected_output_structure=recursive_schema)

    # Should pass without RecursionError during validation logic itself
    assert case.expected_output_structure is not None


def test_bec_manifest_duplicate_case_ids() -> None:
    """
    Edge Case: The PRD Memory states "BECManifest allows duplicate id values in its cases list."
    We should verify this explicitly to ensure we haven't accidentally enforced uniqueness
    where it wasn't requested (unlike Topology).
    """
    case1 = BECTestCase(id="same-id", prompt="A")
    case2 = BECTestCase(id="same-id", prompt="B")

    manifest = BECManifest(corpus_id="corpus-dupes", cases=[case1, case2])

    assert len(manifest.cases) == 2
    assert manifest.cases[0].id == "same-id"
    assert manifest.cases[1].id == "same-id"


def test_bectestcase_empty_context_list() -> None:
    """
    Edge Case: Empty context_files list should be valid and result in empty list.
    """
    case = BECTestCase(id="empty-context", prompt="No context", context_files=[])
    assert case.context_files == []


def test_bectestcase_none_context_fails() -> None:
    """
    Edge Case: explicit None for context_files should fail (list required).
    """
    with pytest.raises(ValidationError):
        BECTestCase(
            id="none-context",
            prompt="Fail",
            context_files=None,
        )
