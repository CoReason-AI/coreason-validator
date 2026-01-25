# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from coreason_validator.schemas.knowledge import EnrichmentLevel, KnowledgeArtifact
from coreason_veritas.policies.data_quality import QualityPolicy


def test_policy_reject_raw() -> None:
    """Test that RAW artifacts are rejected."""
    artifact = KnowledgeArtifact(
        id="123", content="test", source_urn="urn:s3:file", enrichment_level=EnrichmentLevel.RAW
    )
    result = QualityPolicy.inspect_artifact(artifact)
    assert result["allowed"] is False
    assert "processed by coreason-tagger" in result["reason"]


def test_policy_reject_bad_urn() -> None:
    """Test that artifacts with invalid URNs are rejected."""
    artifact = KnowledgeArtifact(
        id="123", content="test", source_urn="https://example.com", enrichment_level=EnrichmentLevel.TAGGED
    )
    result = QualityPolicy.inspect_artifact(artifact)
    assert result["allowed"] is False
    assert "URN standard" in result["reason"]


def test_policy_allow_compliant() -> None:
    """Test that compliant artifacts are allowed."""
    artifact = KnowledgeArtifact(
        id="123", content="test", source_urn="urn:s3:file", enrichment_level=EnrichmentLevel.TAGGED
    )
    result = QualityPolicy.inspect_artifact(artifact)
    assert result["allowed"] is True
    assert result["reason"] == "Compliant"
