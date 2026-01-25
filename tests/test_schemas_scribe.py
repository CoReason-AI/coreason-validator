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
from coreason_validator.schemas.scribe import DocumentationManifest, ReviewPacket, TraceabilityMatrix
from pydantic import ValidationError


def test_valid_documentation_manifest() -> None:
    matrix = TraceabilityMatrix(req_id="REQ-001", test_ids=["TEST-001", "TEST-002"], coverage_status="COVERED")
    manifest = DocumentationManifest(agent_version="1.0.0", bom_hash="abc123hash", matrix=[matrix])
    assert manifest.agent_version == "1.0.0"
    assert manifest.matrix[0].req_id == "REQ-001"


def test_valid_review_packet() -> None:
    packet = ReviewPacket(
        packet_id="packet-1",
        agent_name="agent-1",
        original_content="original",
        generated_content="generated",
        diff_summary="summary",
        risk_score=0.5,
    )
    assert packet.risk_score == 0.5


def test_invalid_review_packet_risk_score() -> None:
    with pytest.raises(ValidationError):
        ReviewPacket(
            packet_id="packet-1",
            agent_name="agent-1",
            original_content="original",
            generated_content="generated",
            diff_summary="summary",
            risk_score=1.5,
        )

    with pytest.raises(ValidationError):
        ReviewPacket(
            packet_id="packet-1",
            agent_name="agent-1",
            original_content="original",
            generated_content="generated",
            diff_summary="summary",
            risk_score=-0.1,
        )
