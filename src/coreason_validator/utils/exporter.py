# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


import json
from pathlib import Path
from typing import Type

from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.schemas.base import CoReasonBaseModel
from coreason_validator.schemas.bec import BECManifest
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.schemas.topology import TopologyGraph
from coreason_validator.utils.logger import logger


def export_json_schemas(output_dir: Path) -> None:
    """
    Exports JSON schemas for all core models to the specified directory.

    Args:
        output_dir: The directory where schema files will be saved.
                    Will be created if it does not exist.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Exporting JSON schemas to: {output_dir}")

    schemas: dict[str, Type[CoReasonBaseModel]] = {
        "agent": AgentManifest,
        "topology": TopologyGraph,
        "bec": BECManifest,
        "tool": ToolCall,
    }

    for name, model_class in schemas.items():
        filename = f"{name}.schema.json"
        file_path = output_dir / filename

        logger.debug(f"Generating schema for {name} ({model_class.__name__})")

        # model_json_schema returns a dict representing the JSON schema
        json_schema = model_class.model_json_schema()

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_schema, f, indent=2, sort_keys=True)
                # Ensure a newline at EOF
                f.write("\n")
            logger.info(f"Exported {filename}")
        except Exception as e:
            logger.error(f"Failed to write schema for {name}: {e}")
            raise
