from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolCall(BaseModel):
    """
    Defines the strict inputs for coreason-mcp.
    Ensures type strictness and prevents SQL injection.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    tool_name: str = Field(..., min_length=1, description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(..., description="Dictionary of arguments for the tool")

    @field_validator("arguments")
    @classmethod
    def check_sql_injection(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scans all string values in arguments for SQL injection patterns.
        """
        # Basic list of dangerous SQL patterns (case-insensitive)
        dangerous_patterns = [
            "DROP TABLE",
            "DELETE FROM",
            "INSERT INTO",
            "UPDATE ",
            "ALTER TABLE",
            "UNION SELECT",
            " OR 1=1",
            "--",  # Comment
        ]

        def scan_value(val: Any, key_path: str) -> None:
            if isinstance(val, str):
                upper_val = val.upper()
                for pattern in dangerous_patterns:
                    if pattern in upper_val:
                        raise ValueError(f"Potential SQL injection detected in field '{key_path}': {pattern}")
            elif isinstance(val, dict):
                for k, sub_val in val.items():
                    scan_value(sub_val, f"{key_path}.{k}")
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    scan_value(item, f"{key_path}[{i}]")

        for key, value in v.items():
            scan_value(value, key)

        return v
