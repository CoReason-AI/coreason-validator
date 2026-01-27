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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import jsonschema
import yaml
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from coreason_identity.models import UserContext
from coreason_validator.registry import registry
from coreason_validator.schemas.base import CoReasonBaseModel
from coreason_validator.schemas.message import Message
from coreason_validator.schemas.tool import ToolCall
from coreason_validator.utils.logger import logger

T = TypeVar("T", bound=CoReasonBaseModel)


class ValidationResult(BaseModel):
    """
    Structured result of a static file validation.
    """

    model_config = ConfigDict(frozen=True)

    is_valid: bool
    # Use Any for model to avoid Pydantic truncating fields when serializing polymorphic models
    # if the base class has no fields. Or use Union of all known models.
    # Using Any is safest for now to ensure model_dump_json works.
    model: Optional[Any] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    validation_metadata: Dict[str, Any] = Field(default_factory=dict)


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


def validate_object(
    data: Dict[str, Any], schema_type: Union[Type[T], str], user_context: Optional[UserContext] = None
) -> T:
    """
    Validates a dictionary against a Pydantic schema class or a string alias.

    1. Sanitizes inputs (trims whitespace, strips null bytes).
    2. Resolves schema if string alias is provided.
    3. Validates against the provided schema.
    4. Returns the validated model instance or raises ValidationError.

    Args:
        data: The input dictionary.
        schema_type: The Pydantic model class (must inherit from CoReasonBaseModel) or a string alias.
        user_context: Optional user identity context.

    Returns:
        An instance of the schema class.

    Raises:
        ValidationError: If validation fails.
        ValueError: If schema_type is invalid.
    """
    schema_class: Type[T]

    if isinstance(schema_type, str):
        found_class = registry.get_schema(schema_type)
        if not found_class:
            raise ValueError(f"Unknown schema type alias: '{schema_type}'")
        # We need to cast because T is bound to CoReasonBaseModel but mypy needs help
        schema_class = found_class  # type: ignore
    elif isinstance(schema_type, type) and issubclass(schema_type, CoReasonBaseModel):
        schema_class = schema_type
    else:
        raise ValueError("Invalid schema_type argument. Must be a CoReasonBaseModel subclass or a string alias.")

    logger.debug(f"Validating object against schema {schema_class.__name__}")

    clean_data = sanitize_inputs(data)

    try:
        instance = schema_class.model_validate(clean_data)
        logger.debug(f"Validation successful for {schema_class.__name__}")
        return instance
    except ValidationError as e:
        logger.error(f"Validation failed for {schema_class.__name__}: {e}")
        raise


def validate_tool_call(tool_call_data: Dict[str, Any]) -> ToolCall:
    """
    Validates a tool call payload.
    A wrapper around validate_object specifically for ToolCall.

    Args:
        tool_call_data: The dictionary containing tool name and arguments.

    Returns:
        Validated ToolCall object.

    Raises:
        ValidationError: If validation fails.
    """
    return validate_object(tool_call_data, ToolCall)


def validate_message(message_data: Dict[str, Any]) -> Message:
    """
    Validates an inter-agent message payload.
    A wrapper around validate_object specifically for Message.

    Args:
        message_data: The dictionary containing message fields.

    Returns:
        Validated Message object.

    Raises:
        ValidationError: If validation fails.
    """
    return validate_object(message_data, Message)


def check_compliance(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validates a JSON object against a JSON schema.
    Used by Assay to check if an Agent's output complies with the BEC expected structure.

    Args:
        instance: The actual output from the agent (Dict).
        schema: The JSON Schema defining expected structure (Dict).

    Raises:
        ValueError: If the instance does not comply with the schema.
    """
    logger.debug("Checking compliance against JSON Schema")

    # Sanitize input first
    clean_instance = sanitize_inputs(instance)

    try:
        jsonschema.validate(instance=clean_instance, schema=schema)
        logger.debug("Compliance check passed")
    except JsonSchemaValidationError as e:
        # e.message contains the specific validation error
        # e.json_path/path/schema_path help locate it
        path_str = " -> ".join(str(p) for p in e.path) if e.path else "Root"
        error_msg = f"Compliance check failed at [{path_str}]: {e.message}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        logger.error(f"Unexpected error during compliance check: {e}")
        raise ValueError(f"Compliance check failed: {str(e)}") from e


def validate_file(
    path: Union[str, Path],
    schema_type: Optional[Union[Type[CoReasonBaseModel], str]] = None,
    user_context: Optional[UserContext] = None,
) -> ValidationResult:
    """
    Reads a file (JSON/YAML), detects the schema type (if not provided), and validates it.

    Args:
        path: Path to the file.
        schema_type: The Pydantic model class, or a string alias ('agent', 'topology', 'bec', 'tool'), or None to infer.
        user_context: Optional user identity context.

    Returns:
        ValidationResult object containing status, the model (if valid), and structured errors.
    """
    # Prepare metadata
    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if user_context:
        metadata["validated_by"] = f"{user_context.user_id} ({user_context.email})"
        metadata["signature_context"] = "Authenticated via CoReason Identity"
    else:
        metadata["validated_by"] = "SYSTEM_AUTOMATION"
        metadata["signature_context"] = "Unattributed"

    path = Path(path)
    logger.info(f"Validating file: {path}")

    if not path.exists():
        logger.error(f"File not found: {path}")
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False, errors=[{"msg": f"File not found: {path}"}], validation_metadata=metadata
        )

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
                    metadata["validation_status"] = "FAIL"
                    return ValidationResult(
                        is_valid=False,
                        errors=[{"msg": f"Unsupported file extension '{suffix}' and failed to auto-parse."}],
                        validation_metadata=metadata,
                    )
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.error(f"Parse error in {path}: {e}")
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False, errors=[{"msg": f"Parse error: {str(e)}"}], validation_metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False, errors=[{"msg": f"Error reading file: {str(e)}"}], validation_metadata=metadata
        )

    if not isinstance(content, dict):
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False,
            errors=[{"msg": "File content must be a dictionary object."}],
            validation_metadata=metadata,
        )

    # 2. Resolve Schema
    schema_class: Optional[Type[CoReasonBaseModel]] = None

    if schema_type is None:
        # Inference Logic using Registry
        schema_class = registry.infer_schema(content)
        if not schema_class:
            metadata["validation_status"] = "FAIL"
            return ValidationResult(
                is_valid=False,
                errors=[{"msg": "Could not infer schema type from content."}],
                validation_metadata=metadata,
            )

    elif isinstance(schema_type, (str, type)):
        # Delegate resolution to validate_object's logic, but we need the class for ValidationResult if possible
        # Actually validate_object returns the instance, so we are good.
        pass
    else:
        return ValidationResult(is_valid=False, errors=[{"msg": "Invalid schema_type argument."}])

    # 3. Validate
    try:
        # If schema_type was None, we inferred schema_class.
        # If schema_type was provided, we pass it directly to validate_object.
        target_schema = schema_class if schema_class else schema_type
        # We need to ensure target_schema is not None.

        instance = validate_object(content, target_schema, user_context=user_context)  # type: ignore
        metadata["validation_status"] = "PASS"
        return ValidationResult(is_valid=True, model=instance, validation_metadata=metadata)
    except ValidationError as e:
        # Returns the list of error dicts provided by Pydantic
        # Must catch ValidationError BEFORE ValueError because ValidationError inherits from ValueError in Pydantic V2
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False, errors=[dict(err) for err in e.errors()], validation_metadata=metadata
        )
    except ValueError as e:
        # validate_object raises ValueError for invalid alias
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False, errors=[{"msg": str(e)}], validation_metadata=metadata
        )
    except RecursionError:
        logger.error("Recursion error during validation")
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False,
            errors=[{"msg": "Recursion limit exceeded (possible cyclic reference)"}],
            validation_metadata=metadata,
        )
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        metadata["validation_status"] = "FAIL"
        return ValidationResult(
            is_valid=False, errors=[{"msg": f"Validation error: {str(e)}"}], validation_metadata=metadata
        )
