# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import re
from typing import Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ToolCall(BaseModel):
    """Legacy ToolCall model, not present in coreason-manifest."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str = Field(..., min_length=1)
    arguments: Dict[str, Any]

    @field_validator("arguments")
    @classmethod
    def validate_sql_injection(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Check for SQL injection patterns in arguments."""
        sql_pattern = re.compile(
            r"(?i)\b(drop\s+table|union\s+select|delete\s+from|insert\s+into|update\s+\w+\s+set)\b"
        )

        def check_recursive(data: Any) -> None:
            if isinstance(data, str):
                if sql_pattern.search(data):
                    raise ValueError(f"Potential SQL injection detected: {data}")
            elif isinstance(data, dict):
                for val in data.values():
                    check_recursive(val)
            elif isinstance(data, (list, tuple)):
                for item in data:
                    check_recursive(item)

        check_recursive(v)
        return v

class Message(BaseModel):
    """Legacy Message model, not present in coreason-manifest."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1)
    sender: str = Field(..., min_length=1)
    receiver: str = Field(..., min_length=1)
    timestamp: datetime
    type: str = Field(..., min_length=1)
    content: Any
