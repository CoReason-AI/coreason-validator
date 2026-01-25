# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from fastapi.testclient import TestClient

from coreason_veritas.server import app

client = TestClient(app)


def test_audit_endpoint_allowed() -> None:
    """Test the audit endpoint with a compliant artifact."""
    payload = {
        "id": "123",
        "content": "test",
        "source_urn": "urn:s3:file",
        "enrichment_level": "TAGGED",
    }
    response = client.post("/audit/artifact", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "status": "approved",
        "policy_id": "104",
        "reason": "Compliant",
    }


def test_audit_endpoint_rejected() -> None:
    """Test the audit endpoint with a non-compliant artifact."""
    payload = {
        "id": "123",
        "content": "test",
        "source_urn": "urn:s3:file",
        "enrichment_level": "RAW",
    }
    response = client.post("/audit/artifact", json=payload)
    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "rejected"
    assert "coreason-tagger" in data["reason"]
