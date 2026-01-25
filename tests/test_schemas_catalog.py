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
from coreason_validator.schemas.catalog import DataSensitivity, SourceManifest
from pydantic import ValidationError


def test_valid_source_manifest() -> None:
    manifest = SourceManifest(
        urn="urn:coreason:mcp:test_source",
        name="Test Source",
        description="A test source",
        endpoint_url="https://api.example.com",
        geo_location="US",
        sensitivity=DataSensitivity.PUBLIC,
        access_policy="allow all",
    )
    assert manifest.urn == "urn:coreason:mcp:test_source"
    assert manifest.sensitivity == DataSensitivity.PUBLIC


def test_invalid_urn_pattern() -> None:
    with pytest.raises(ValidationError):
        SourceManifest(
            urn="invalid_urn",
            name="Test Source",
            description="A test source",
            endpoint_url="https://api.example.com",
            geo_location="US",
            sensitivity=DataSensitivity.PUBLIC,
            access_policy="allow all",
        )


def test_invalid_sensitivity() -> None:
    with pytest.raises(ValidationError):
        SourceManifest(
            urn="urn:coreason:mcp:test_source",
            name="Test Source",
            description="A test source",
            endpoint_url="https://api.example.com",
            geo_location="US",
            sensitivity="INVALID",
            access_policy="allow all",
        )
