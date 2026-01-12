# coreason-validator

Enforces structural integrity across the entire CoReason ecosystem

[![CI](https://github.com/CoReason-AI/coreason_validator/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason_validator/actions/workflows/ci.yml)

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

### Development Usage

-   Run the linter:
    ```sh
    poetry run pre-commit run --all-files
    ```
-   Run the tests:
    ```sh
    poetry run pytest
    ```
