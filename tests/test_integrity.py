# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any, Dict, List

from pydantic import ConfigDict

from coreason_validator.schemas.base import CoReasonBaseModel


class ComplexModel(CoReasonBaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    data: Dict[str, Any]
    items: List[Dict[str, Any]]


def test_recursive_sorting_integrity() -> None:
    """
    Verifies that canonical_hash handles recursive sorting of nested keys.
    """
    # Object A: Keys intentionally disordered
    obj_a = ComplexModel(
        data={"b": 1, "a": 2, "nested": {"z": 10, "y": 20}}, items=[{"y": 100, "x": 200}, {"b": 300, "a": 400}]
    )

    # Object B: Keys ordered differently but semantically identical
    obj_b = ComplexModel(
        data={"a": 2, "b": 1, "nested": {"y": 20, "z": 10}}, items=[{"x": 200, "y": 100}, {"a": 400, "b": 300}]
    )

    hash_a = obj_a.canonical_hash()
    hash_b = obj_b.canonical_hash()

    assert hash_a == hash_b
