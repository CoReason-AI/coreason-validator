# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Literal

from coreason_validator.registry import SchemaRegistry, registry
from pydantic import BaseModel as CoReasonBaseModel
from coreason_validator.validator import validate_object


class MockSchemaA(CoReasonBaseModel):
    kind: Literal["A"]
    value: int


class MockSchemaB(CoReasonBaseModel):
    kind: Literal["B"]
    value: int


class AmbiguousSchema(CoReasonBaseModel):
    # Matches both A and B pattern conceptually for the test
    kind: str
    value: int


def test_registry_case_insensitivity() -> None:
    """
    Verify that the registry handles aliases case-insensitively.
    """
    local_registry = SchemaRegistry()
    local_registry.register("MixedCase", MockSchemaA)

    assert local_registry.get_schema("mixedcase") == MockSchemaA
    assert local_registry.get_schema("MIXEDCASE") == MockSchemaA
    assert local_registry.get_schema("MixedCase") == MockSchemaA


def test_registry_override_alias() -> None:
    """
    Verify that registering a new schema with an existing alias overwrites the old one.
    This allows for hot-swapping schemas if needed.
    """
    local_registry = SchemaRegistry()
    local_registry.register("test", MockSchemaA)
    assert local_registry.get_schema("test") == MockSchemaA

    local_registry.register("test", MockSchemaB)
    assert local_registry.get_schema("test") == MockSchemaB


def test_registry_inference_priority() -> None:
    """
    Verify behavior when multiple detectors match.
    Since Python 3.7+, dicts preserve insertion order. The registry iterates sequentially.
    The first matching detector should win.
    """
    local_registry = SchemaRegistry()

    # Register Schema A to match if "common_key" is present
    local_registry.register("a", MockSchemaA, lambda d: "common_key" in d and d.get("kind") == "A")

    # Register Schema B to match if "common_key" is present
    local_registry.register("b", MockSchemaB, lambda d: "common_key" in d)

    input_data = {"common_key": "exists", "kind": "A", "value": 1}

    # Should match A because it was registered first and matches
    assert local_registry.infer_schema(input_data) == MockSchemaA

    # New registry where B is registered first
    local_registry_2 = SchemaRegistry()
    local_registry_2.register("b", MockSchemaB, lambda d: "common_key" in d)
    local_registry_2.register("a", MockSchemaA, lambda d: "common_key" in d and d.get("kind") == "A")

    # Should match B because it's checked first and the condition "common_key" in d is True
    assert local_registry_2.infer_schema(input_data) == MockSchemaB


def test_complex_dynamic_runtime_extension() -> None:
    """
    Complex Scenario:
    1. Define a new schema at runtime.
    2. Register it with the global registry (using a cleanup fixture or manual reset).
    3. Use validate_object with the string alias to ensure the decoupling works.
    """

    # 1. Define runtime schema
    class RuntimeSchema(CoReasonBaseModel):
        dynamic_field: str

    # 2. Register with global registry
    # We use a unique alias to avoid clashing with other tests running in parallel
    # (though pytest is usually sequential per worker)
    alias = "runtime_extension_test"
    registry.register(alias, RuntimeSchema, lambda d: "dynamic_field" in d)

    try:
        # 3. Test Inference via global registry access implicitly used by systems
        # Note: validate_object calls registry.get_schema if we pass a string.
        # But we want to test that validate_object finds it.

        data = {"dynamic_field": "hello world"}

        # Test explicit alias lookup validation
        # Annotate as CoReasonBaseModel because validate_object returns T (CoReasonBaseModel)
        # when passed a string alias.
        result: CoReasonBaseModel = validate_object(data, alias)

        assert isinstance(result, RuntimeSchema)
        assert result.dynamic_field == "hello world"

        # Test inference support
        # We need to simulate the inference call. `validate_object` doesn't do inference itself,
        # but `validate_file` does. We can test registry.infer_schema directly or mock validate_file flow.
        # Let's test registry.infer_schema directly as it's the unit under test.
        inferred_cls = registry.infer_schema(data)
        assert inferred_cls == RuntimeSchema

    finally:
        # Cleanup: Remove the entry to avoid side effects
        if alias in registry._schemas:
            del registry._schemas[alias]
        if alias in registry._detectors:
            del registry._detectors[alias]


def test_registry_unknown_alias() -> None:
    """
    Verify graceful handling of unknown aliases.
    """
    local_registry = SchemaRegistry()
    assert local_registry.get_schema("non_existent") is None


def test_registry_no_inference_match() -> None:
    """
    Verify inference returns None when no detector matches.
    """
    local_registry = SchemaRegistry()
    local_registry.register("a", MockSchemaA, lambda d: "kind" in d)

    assert local_registry.infer_schema({"other": "field"}) is None
