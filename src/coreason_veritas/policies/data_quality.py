# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any, Dict

from coreason_validator.schemas.knowledge import EnrichmentLevel, KnowledgeArtifact


class QualityPolicy:
    @staticmethod
    def inspect_artifact(artifact: KnowledgeArtifact) -> Dict[str, Any]:
        """
        Enforces Policy #104: Minimum Enrichment Standards.
        Returns: {'allowed': bool, 'reason': str}
        """
        # Rule 1: Must be TAGGED or LINKED. RAW is forbidden in production memory.
        if artifact.enrichment_level == EnrichmentLevel.RAW:
            return {
                "allowed": False,
                "reason": "Artifact is RAW. Must be processed by coreason-tagger.",
            }

        # Rule 2: Must have a valid Source URN
        if not artifact.source_urn.startswith("urn:"):
            return {
                "allowed": False,
                "reason": "Invalid Provenance. Source URN must adhere to URN standard.",
            }

        return {"allowed": True, "reason": "Compliant"}
