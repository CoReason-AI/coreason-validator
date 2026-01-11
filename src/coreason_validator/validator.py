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
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from coreason_validator.schemas.agent import AgentManifest
from coreason_validator.schemas.base import CoReasonBaseModel
from coreason_validator.schemas.bec import BECManifest
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.schemas.topology import TopologyGraph
from coreason_validator.utils.logger import logger

T = TypeVar("T", bound=CoReasonBaseModel)


class ValidationResult(BaseModel):
    """
    Structured result of a static file validation.
    """

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    model: Optional[CoReasonBaseModel] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)


def sanitize_inputs(data: Any) -> Any:
    """
    Recursively sanitizes input data.
    - Trims whitespace from strings.
    - Strips null bytes ('\0') from strings.
    - Handles nested dictionaries, lists, tuples, and sets.
    """
    if isinstance(data, str):
        # Strip null bytes and trim whitespace
        return data.replace("\0", "").strip()
    if isinstance(data, dict):
        return {k: sanitize_inputs(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_inputs(i) for i in data]
    if isinstance(data, tuple):
        return tuple(sanitize_inputs(i) for i in data)
    if isinstance(data, set):
        return {sanitize_inputs(i) for i in data}
    return data


def validate_object(data: Dict[str, Any], schema: Type[T]) -> T:
    """
    Validates a dictionary against a Pydantic schema class.

    1. Sanitizes inputs (trims whitespace, strips null bytes).
    2. Validates against the provided schema.
    3. Returns the validated model instance or raises ValidationError.

    Args:
        data: The input dictionary.
        schema: The Pydantic model class (must inherit from CoReasonBaseModel).

    Returns:
        An instance of the schema class.

    Raises:
        ValidationError: If validation fails.
    """
    logger.debug(f"Validating object against schema {schema.__name__}")

    clean_data = sanitize_inputs(data)

    try:
        instance = schema.model_validate(clean_data)
        logger.debug(f"Validation successful for {schema.__name__}")
        return instance
    except ValidationError as e:
        logger.error(f"Validation failed for {schema.__name__}: {e}")
        raise


def validate_file(
    path: Union[str, Path], schema_type: Optional[Union[Type[CoReasonBaseModel], str]] = None
) -> ValidationResult:
    """
    Reads a file (JSON/YAML), detects the schema type (if not provided), and validates it.

    Args:
        path: Path to the file.
        schema_type: The Pydantic model class, or a string alias ('agent', 'topology', 'bec', 'tool'), or None to infer.

    Returns:
        ValidationResult object containing status, the model (if valid), and structured errors.
    """
    path = Path(path)
    logger.info(f"Validating file: {path}")

    if not path.exists():
        logger.error(f"File not found: {path}")
        return ValidationResult(is_valid=False, errors=[{"msg": f"File not found: {path}"}])

    # 1. Read & Parse
    content: Any = None
    try:
        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            content = yaml.safe_load(text)
        elif suffix == ".json":
            content = json.loads(text)
        else:
            # Try parsing as JSON first, then YAML
            try:
                content = json.loads(text)
            except json.JSONDecodeError:
                try:
                    content = yaml.safe_load(text)
                except yaml.YAMLError:
                    return ValidationResult(
                        is_valid=False,
                        errors=[{"msg": f"Unsupported file extension '{suffix}' and failed to auto-parse."}],
                    )
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.error(f"Parse error in {path}: {e}")
        return ValidationResult(is_valid=False, errors=[{"msg": f"Parse error: {str(e)}"}])
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return ValidationResult(is_valid=False, errors=[{"msg": f"Error reading file: {str(e)}"}])

    if not isinstance(content, dict):
        return ValidationResult(is_valid=False, errors=[{"msg": "File content must be a dictionary object."}])

    # 2. Resolve Schema
    schema_class: Optional[Type[CoReasonBaseModel]] = None

    if isinstance(schema_type, type) and issubclass(schema_type, CoReasonBaseModel):
        schema_class = schema_type
    elif isinstance(schema_type, str):
        lookup: Dict[str, Type[CoReasonBaseModel]] = {
            "agent": AgentManifest,
            "topology": TopologyGraph,
            "bec": BECManifest,
            "tool": ToolCall,
        }
        schema_class = lookup.get(schema_type.lower())
        if not schema_class:
            return ValidationResult(is_valid=False, errors=[{"msg": f"Unknown schema type alias: '{schema_type}'"}])
    elif schema_type is None:
        # Inference Logic
        if "model_config" in content:
            schema_class = AgentManifest
        elif "corpus_id" in content:
            schema_class = BECManifest
        elif "nodes" in content:
            schema_class = TopologyGraph
        elif "tool_name" in content:
            schema_class = ToolCall
        else:
            return ValidationResult(is_valid=False, errors=[{"msg": "Could not infer schema type from content."}])
    else:
        return ValidationResult(is_valid=False, errors=[{"msg": "Invalid schema_type argument."}])

    # 3. Validate
    try:
        instance = validate_object(content, schema_class)
        return ValidationResult(is_valid=True, model=instance)
    except ValidationError as e:
        # Returns the list of error dicts provided by Pydantic
        # Convert TypedDict to dict for Mypy compatibility if needed, though usually compatible.
        # But Mypy complained, so we explicitly cast/copy.
        return ValidationResult(is_valid=False, errors=[dict(err) for err in e.errors()])
