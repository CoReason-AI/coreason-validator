# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


from coreason_validator.schemas.knowledge import KnowledgeArtifact


def test_empty_strings() -> None:
    """Test instantiation with empty strings for required fields."""
    artifact = KnowledgeArtifact(id="", content="", source_urn="")
    assert artifact.id == ""
    assert artifact.content == ""
    assert artifact.source_urn == ""


def test_long_strings() -> None:
    """Test instantiation with very long strings."""
    long_string = "a" * 10000
    artifact = KnowledgeArtifact(id=long_string, content=long_string, source_urn=long_string)
    assert artifact.id == long_string
    assert artifact.content == long_string
    assert artifact.source_urn == long_string


def test_special_characters() -> None:
    """Test instantiation with special characters."""
    special_str = "ñ~!@#$%^&*()_+|}{[]:\"';<>?,./`"
    artifact = KnowledgeArtifact(id=special_str, content=special_str, source_urn=special_str)
    assert artifact.id == special_str
    assert artifact.content == special_str
    assert artifact.source_urn == special_str


def test_source_location_nested() -> None:
    """Test complex nested dictionaries in source_location."""
    location = {
        "page": 1,
        "bbox": [0, 10, 100, 200],
        "meta": {"author": "me", "timestamp": 12345},
        "nested": {"deep": {"deeper": "value"}},
    }
    artifact = KnowledgeArtifact(id="1", content="test", source_urn="urn:1", source_location=location)
    assert artifact.source_location == location


def test_vector_edge_cases() -> None:
    """Test vector edge cases."""
    # Empty list
    a1 = KnowledgeArtifact(id="1", content="c", source_urn="u", vector=[])
    assert a1.vector == []

    # Large dimension
    large_vec = [0.1] * 1536
    a2 = KnowledgeArtifact(id="2", content="c", source_urn="u", vector=large_vec)
    assert a2.vector == large_vec

    # Negative values
    neg_vec = [-0.1, -0.5]
    a3 = KnowledgeArtifact(id="3", content="c", source_urn="u", vector=neg_vec)
    assert a3.vector == neg_vec


def test_tags_edge_cases() -> None:
    """Test tags edge cases."""
    # Duplicates (List allows duplicates unless validator enforces set)
    tags = ["tag1", "tag1", "tag2"]
    artifact = KnowledgeArtifact(id="1", content="c", source_urn="u", tags=tags)
    assert artifact.tags == tags

    # Empty strings
    tags_empty = ["", "   "]
    artifact2 = KnowledgeArtifact(id="2", content="c", source_urn="u", tags=tags_empty)
    assert artifact2.tags == tags_empty


def test_sensitivity_arbitrary_string() -> None:
    """Test that sensitivity accepts any string (since it's not an Enum)."""
    artifact = KnowledgeArtifact(id="1", content="c", source_urn="u", sensitivity="TOP_SECRET_EYES_ONLY")
    assert artifact.sensitivity == "TOP_SECRET_EYES_ONLY"
