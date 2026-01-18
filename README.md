# coreason-validator

[![CI](https://github.com/CoReason-AI/coreason_validator/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason_validator/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Prosperity%203.0-blue.svg)](https://prosperitylicense.com/versions/3.0.0)
[![Python](https://img.shields.io/badge/python-3.12%20|%203.13%20|%203.14-blue)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/CoReason-AI/coreason_validator/graph/badge.svg?token=placeholder)](https://codecov.io/gh/CoReason-AI/coreason_validator)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

Enforces structural integrity across the entire CoReason ecosystem.

## Overview

`coreason-validator` acts as the **Single Source of Truth** for all data structures (Agents, Tests, Topologies, Messages). It provides "Schemas-as-Code" definitions and validation logic to check assets *before* they are processed, ensuring structural soundness.

In a GxP environment, "Implicit Trust" is a vulnerability. Component A must never assume Component B sent valid data. This library ensures that what *is about to happen* is structurally sound.

## Key Features

*   **Schema Registry**: A collection of immutable Pydantic Models defining valid assets.
*   **Static Analyzer**: A validation engine that runs on static files (JSON/YAML) with rich error reporting.
*   **Runtime Guard**: A lightweight validation function for dynamic payloads with microsecond latency.
*   **Integrity Hasher**: Provides canonical hashing to ensure file integrity and GxP compliance.
*   **Frontend Bridge**: Exports JSON Schemas to keep the UI in sync with the backend.

## Documentation

For detailed documentation, please refer to the `docs/` directory or the hosted site:

-   [Usage Guide](docs/usage.md)
-   [Architecture](docs/architecture.md)
-   [Product Requirements](docs/requirements.md)

## Architecture

The library implements the **Define-Check-Hash Loop**:
1.  **Define**: Schemas as strict Python classes (Pydantic V2).
2.  **Check**: Shift-left validation locally and at runtime.
3.  **Hash**: Canonical hashing of the validated structure for GxP integrity.

See [Architecture](docs/architecture.md) for more details.

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry

### Installation

1.  Clone the repository:
    ```sh
    git clone https://github.com/CoReason-AI/coreason_validator.git
    cd coreason_validator
    ```
2.  Install dependencies:
    ```sh
    poetry install
    ```

## Usage

### CLI Quick Start

The package exposes a CLI tool `coreason-val` for validation and schema operations.

#### Validate a File

To validate a YAML or JSON file against its schema (schema type is auto-detected):

```sh
poetry run coreason-val check path/to/file.yaml
```

**Example:**
```sh
poetry run coreason-val check samples/agent_config.yaml
```

#### Export JSON Schemas

To export the canonical JSON Schemas for use in other systems (e.g., Frontend forms):

```sh
poetry run coreason-val export ./schemas_out
```

This will generate `agent.schema.json`, `bec.schema.json`, etc., in the specified directory.

### Python API

For deep integration, import `coreason_validator` directly.

```python
from coreason_validator import validate_file, validate_object

# Validate a file
result = validate_file("path/to/agent.yaml")
if result.is_valid:
    print("Valid!")
else:
    print(f"Errors: {result.errors}")

# Validate an object (Runtime)
data = {"name": "my-agent", "version": "1.0.0"}
try:
    model = validate_object(data, "agent")
    print(f"Canonical Hash: {model.canonical_hash()}")
except Exception as e:
    print(f"Validation failed: {e}")
```

## Development

-   Run the linter:
    ```sh
    poetry run pre-commit run --all-files
    ```
-   Run the tests:
    ```sh
    poetry run pytest
    ```
-   Build documentation:
    ```sh
    poetry run mkdocs build
    ```
