# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from coreason_validator.schemas.audit import SignatureEvent, SignatureRole


def test_valid_signature_event() -> None:
    event = SignatureEvent(
        document_hash="sha256:1234567890abcdef",
        signer_id="user:123",
        role=SignatureRole.AUTHOR,
        meaning="I approve",
        timestamp=datetime.now(timezone.utc),
        crypto_token="token123",
    )
    assert event.role == SignatureRole.AUTHOR
    assert event.signer_id == "user:123"


def test_invalid_signature_role() -> None:
    with pytest.raises(ValidationError):
        SignatureEvent(
            document_hash="sha256:123",
            signer_id="user:123",
            role="INVALID_ROLE",
            meaning="test",
            timestamp=datetime.now(timezone.utc),
            crypto_token="token",
        )


def test_signature_event_canonical_hash() -> None:
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    event = SignatureEvent(
        document_hash="hash1",
        signer_id="user1",
        role=SignatureRole.APPROVER,
        meaning="meaning1",
        timestamp=dt,
        crypto_token="token1",
    )
    # Check that canonical_hash works
    assert isinstance(event.canonical_hash(), str)
    assert len(event.canonical_hash()) == 64
