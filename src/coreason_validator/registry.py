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

from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.schemas.base import CoReasonBaseModel
from coreason_validator.schemas.bec import BECManifest
from coreason_validator.schemas.message import Message
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.schemas.topology import TopologyGraph


class SchemaRegistry:
    """
    Registry for CoReason schemas.
    Handles schema lookup by alias and automatic inference based on content.
    """

    def __init__(self) -> None:
        self._alias_map: Dict[str, Type[CoReasonBaseModel]] = {}
        self._detectors: Dict[Type[CoReasonBaseModel], Callable[[Dict[str, Any]], bool]] = {}

    def register(
        self,
        alias: str,
        schema_cls: Type[CoReasonBaseModel],
        detector: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> None:
        """
        Registers a schema class with an alias and an optional detection function.

        Args:
            alias: The string alias for the schema (case-insensitive).
            schema_cls: The Pydantic model class.
            detector: A function that returns True if a given dictionary matches this schema.
        """
        self._alias_map[alias.lower()] = schema_cls
        if detector:
            self._detectors[schema_cls] = detector

    def get_schema(self, alias: str) -> Optional[Type[CoReasonBaseModel]]:
        """
        Retrieves a schema class by its alias.

        Args:
            alias: The string alias.

        Returns:
            The schema class or None if not found.
        """
        return self._alias_map.get(alias.lower())

    def infer_schema(self, data: Dict[str, Any]) -> Optional[Type[CoReasonBaseModel]]:
        """
        Infers the schema type based on the content of the dictionary.

        Args:
            data: The input dictionary.

        Returns:
            The matching schema class or None if no match is found.
        """
        for schema_cls, detector in self._detectors.items():
            if detector(data):
                return schema_cls
        return None


# Global Registry Instance
registry = SchemaRegistry()

# Register known schemas
registry.register("agent", AgentManifest, lambda d: "model_config" in d)
registry.register("bec", BECManifest, lambda d: "corpus_id" in d)
registry.register("topology", TopologyGraph, lambda d: "nodes" in d)
registry.register("tool", ToolCall, lambda d: "tool_name" in d)
registry.register("message", Message)
