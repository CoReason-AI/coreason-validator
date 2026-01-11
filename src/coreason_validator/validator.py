# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Any, Dict, Type, TypeVar

from pydantic import ValidationError

from coreason_validator.schemas.base import CoReasonBaseModel
from coreason_validator.utils.logger import logger

T = TypeVar("T", bound=CoReasonBaseModel)


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
