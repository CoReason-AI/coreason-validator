# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import os
import sys

from loguru import logger

# Configuration from Environment Variables
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")

# Remove default handler
logger.remove()

# Add Console Handler (stderr)
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)

# Add File Handler (JSON formatted)
# Ensure directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# We use 'serialize=True' for built-in JSON, but AGENTS.md implies JSON-formatted.
# Loguru's serialize=True does a good job.
logger.add(
    LOG_FILE_PATH,
    level=LOG_LEVEL,
    rotation="500 MB",  # or "1 day" - AGENTS.md said "500 MB or 1 day", loguru allows one.
    # We can pass retention.
    retention="10 days",
    serialize=True,  # This outputs JSON
    enqueue=True,  # Thread safety
)

# Export logger
__all__ = ["logger"]
