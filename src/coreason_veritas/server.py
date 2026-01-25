# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from loguru import logger

from coreason_validator.schemas.knowledge import KnowledgeArtifact
from coreason_veritas.policies.data_quality import QualityPolicy

app = FastAPI()


@app.post("/audit/artifact")
async def audit_artifact(artifact: KnowledgeArtifact) -> JSONResponse:
    logger.info(f"Auditing artifact: {artifact.id}")
    result = QualityPolicy.inspect_artifact(artifact)

    if result["allowed"]:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "approved", "policy_id": "104", "reason": result["reason"]},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"status": "rejected", "policy_id": "104", "reason": result["reason"]},
        )
