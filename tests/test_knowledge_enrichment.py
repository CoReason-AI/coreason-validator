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

from coreason_validator.schemas.knowledge import EnrichmentLevel, KnowledgeArtifact


def test_knowledge_artifact_default_enrichment() -> None:
    """Test that default enrichment_level is RAW and entities are empty."""
    artifact = KnowledgeArtifact(id="hash123", content="# Content", source_urn="urn:s3:bucket/file.md")
    assert artifact.enrichment_level == EnrichmentLevel.RAW
    assert artifact.entities == []


def test_knowledge_artifact_tagged_enrichment() -> None:
    """Test setting enrichment_level to TAGGED and providing entities."""
    entities = [{"name": "CoReason", "type": "ORG"}, {"name": "AI", "type": "TECH"}]
    artifact = KnowledgeArtifact(
        id="hash456",
        content="CoReason AI",
        source_urn="urn:s3:bucket/file.md",
        enrichment_level=EnrichmentLevel.TAGGED,
        entities=entities,
    )
    assert artifact.enrichment_level == EnrichmentLevel.TAGGED
    assert artifact.entities == entities


def test_knowledge_artifact_linked_enrichment() -> None:
    """Test setting enrichment_level to LINKED."""
    artifact = KnowledgeArtifact(
        id="hash789",
        content="Linked Content",
        source_urn="urn:s3:bucket/file.md",
        enrichment_level=EnrichmentLevel.LINKED,
    )
    assert artifact.enrichment_level == EnrichmentLevel.LINKED


def test_knowledge_artifact_invalid_enrichment_level() -> None:
    """Test validation error for invalid enrichment_level."""
    with pytest.raises(ValidationError):
        KnowledgeArtifact(
            id="hash000",
            content="Invalid Level",
            source_urn="urn:s3:bucket/file.md",
            enrichment_level="INVALID_LEVEL",
        )
