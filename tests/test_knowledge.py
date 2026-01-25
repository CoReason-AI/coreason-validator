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
from coreason_validator.schemas.knowledge import ArtifactType, KnowledgeArtifact
from pydantic import ValidationError


def test_knowledge_artifact_minimal() -> None:
    """Test valid instantiation with minimal required fields."""
    artifact = KnowledgeArtifact(id="hash123", content="# Hello World", source_urn="urn:s3:bucket/file.md")
    assert artifact.id == "hash123"
    assert artifact.content == "# Hello World"
    assert artifact.source_urn == "urn:s3:bucket/file.md"
    assert artifact.artifact_type == ArtifactType.TEXT
    assert artifact.source_location == {}
    assert artifact.vector is None
    assert artifact.tags == []
    assert artifact.sensitivity == "INTERNAL"


def test_knowledge_artifact_full() -> None:
    """Test valid instantiation with all fields."""
    artifact = KnowledgeArtifact(
        id="hash456",
        content="Image data",
        artifact_type=ArtifactType.IMAGE,
        source_urn="urn:s3:bucket/image.png",
        source_location={"page": 1, "bbox": [0, 0, 100, 100]},
        vector=[0.1, 0.2, 0.3],
        tags=["image", "logo"],
        sensitivity="CONFIDENTIAL",
    )
    assert artifact.artifact_type == ArtifactType.IMAGE
    assert artifact.source_location["page"] == 1
    assert artifact.vector == [0.1, 0.2, 0.3]
    assert artifact.tags == ["image", "logo"]
    assert artifact.sensitivity == "CONFIDENTIAL"


def test_knowledge_artifact_missing_required() -> None:
    """Test validation error when missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        KnowledgeArtifact(
            id="hash789",
            # content is missing
            source_urn="urn:s3:bucket/file.txt",  # type: ignore[call-arg]
        )
    assert "content" in str(excinfo.value)


def test_knowledge_artifact_invalid_type() -> None:
    """Test validation error when artifact_type is invalid."""
    with pytest.raises(ValidationError):
        KnowledgeArtifact(
            id="hash000",
            content="Invalid type",
            source_urn="urn:s3:bucket/file.txt",
            artifact_type="AUDIO",  # Invalid enum value
        )
