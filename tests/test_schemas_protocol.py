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
from coreason_validator.schemas.protocol import ProtocolDefinition, PicoBlock, OntologyTerm

def test_valid_protocol_definition():
    term = OntologyTerm(
        id="term1",
        label="Term 1",
        code="T1",
        vocab_source="SNOMED"
    )
    pico = PicoBlock(
        description="Patients with diabetes",
        terms=[term]
    )
    protocol = ProtocolDefinition(
        id="proto1",
        research_question="Does X cause Y?",
        pico_structure={"P": pico},
        status="DRAFT"
    )
    assert protocol.id == "proto1"
    assert protocol.pico_structure["P"].terms[0].code == "T1"
