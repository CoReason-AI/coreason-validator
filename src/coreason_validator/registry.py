# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel

# Import STRICT definitions from the Kernel
from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.definitions.audit import AuditLog
from coreason_manifest.definitions.message import Message, ToolCallRequestPart
from coreason_manifest.definitions.topology import GraphTopology
from coreason_manifest.recipes import RecipeManifest


class SchemaRegistry:
    """
    Registry for CoReason schemas.
    Handles schema lookup by alias and automatic inference based on content.
    """

    def __init__(self) -> None:
        self._schemas: Dict[str, Type[BaseModel]] = {
            "agent": AgentDefinition,
            "tool": ToolCallRequestPart,
            "topology": GraphTopology,
            "recipe": RecipeManifest,
            "audit": AuditLog,
            "message": Message,
        }
        self._detectors: Dict[str, Callable[[Dict[str, Any]], bool]] = {
            "agent": lambda d: "integrity_hash" in d and "config" in d,
            "recipe": lambda d: "topology" in d and "interface" in d,
            "topology": lambda d: "nodes" in d and "edges" in d and "state_schema" in d,
            "audit": lambda d: "audit_id" in d and "trace_id" in d,
            "tool": lambda d: "name" in d and "arguments" in d,
            "message": lambda d: "role" in d and "parts" in d,
        }

    def register(
        self,
        alias: str,
        schema_cls: Type[BaseModel],
        detector: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> None:
        """
        Registers a schema class with an alias and an optional detection function.

        Args:
            alias: The string alias for the schema (case-insensitive).
            schema_cls: The Pydantic model class.
            detector: A function that returns True if a given dictionary matches this schema.
        """
        key = alias.lower()
        self._schemas[key] = schema_cls
        if detector:
            self._detectors[key] = detector

    def get_schema(self, alias: str) -> Optional[Type[BaseModel]]:
        """
        Retrieves a schema class by its alias.

        Args:
            alias: The string alias.

        Returns:
            The schema class or None if not found.
        """
        return self._schemas.get(alias.lower())

    def infer_schema(self, content: Dict[str, Any]) -> Optional[Type[BaseModel]]:
        """
        Infers the schema type based on the content of the dictionary.

        Args:
            content: The input dictionary.

        Returns:
            The matching schema class or None if no match is found.
        """
        # Try to match based on heuristics
        for alias, detector in self._detectors.items():
            if detector(content):
                return self._schemas[alias]
        return None


# Global Registry Instance
registry = SchemaRegistry()
