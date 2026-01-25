# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import json
from typing import List

from coreason_validator.schemas.knowledge import ArtifactType, KnowledgeArtifact


def test_workflow_serialization() -> None:
    """Test full serialization/deserialization loop."""
    original = KnowledgeArtifact(
        id="hash-123",
        content="Complex content with \n newlines and symbols",
        artifact_type=ArtifactType.TABLE,
        source_urn="urn:s3:data.csv",
        source_location={"row": 5, "col": "A"},
        vector=[0.123, 0.456],
        tags=["financial", "q1"],
        sensitivity="HIGH",
    )

    # Serialize
    json_str = original.model_dump_json()
    data = json.loads(json_str)

    # Deserialize
    reconstructed = KnowledgeArtifact.model_validate(data)

    assert original == reconstructed
    assert original.canonical_hash() == reconstructed.canonical_hash()


def test_bulk_creation() -> None:
    """Test creating a batch of artifacts (redundancy check)."""
    artifacts: List[KnowledgeArtifact] = []
    for i in range(100):
        artifacts.append(
            KnowledgeArtifact(
                id=f"id-{i}",
                content=f"content-{i}",
                source_urn="urn:source",
                vector=[float(i), float(i + 1)],
            )
        )
    assert len(artifacts) == 100
    assert artifacts[99].id == "id-99"
    assert artifacts[0].vector == [0.0, 1.0]


def test_combinations_optional_fields() -> None:
    """Test various combinations of optional fields."""
    # Only vector
    a1 = KnowledgeArtifact(id="1", content="c", source_urn="u", vector=[1.0])
    assert a1.vector is not None
    assert a1.tags == []
    assert a1.source_location == {}

    # Only tags
    a2 = KnowledgeArtifact(id="2", content="c", source_urn="u", tags=["t"])
    assert a2.vector is None
    assert a2.tags == ["t"]
    assert a2.source_location == {}

    # Only location
    a3 = KnowledgeArtifact(id="3", content="c", source_urn="u", source_location={"a": 1})
    assert a3.vector is None
    assert a3.tags == []
    assert a3.source_location == {"a": 1}

    # Vector and Tags
    a4 = KnowledgeArtifact(id="4", content="c", source_urn="u", vector=[1.0], tags=["t"])
    assert a4.vector is not None
    assert a4.tags == ["t"]
    assert a4.source_location == {}


def test_canonical_hash_consistency() -> None:
    """Ensure canonical hash is stable across identical instances created differently."""
    # Instance 1: Created with explicit defaults
    a1 = KnowledgeArtifact(
        id="hash",
        content="text",
        source_urn="urn",
        artifact_type=ArtifactType.TEXT,
        tags=[],
        source_location={},
        sensitivity="INTERNAL",
    )

    # Instance 2: Created relying on defaults
    a2 = KnowledgeArtifact(id="hash", content="text", source_urn="urn")

    assert a1 == a2
    assert a1.canonical_hash() == a2.canonical_hash()
