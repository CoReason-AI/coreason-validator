# Usage Guide

`coreason-validator` can be used via the command line interface (CLI) for quick checks and schema exports, or imported as a Python library for integration into runtime applications.

## CLI Usage

The package exposes the `coreason-val` command.

### Validate a File

The `check` command validates a file (JSON or YAML) against its schema. The schema type is auto-detected based on the file content.

```bash
# Validate a YAML file
poetry run coreason-val check path/to/agent.yaml

# Validate a JSON file
poetry run coreason-val check path/to/bec.json

# Output results as JSON (useful for programmatic parsing)
poetry run coreason-val check path/to/agent.yaml --json
```

**Output Example:**
```text
✅ Validation successful: path/to/agent.yaml
```

**Error Example:**
```text
❌ Validation failed: path/to/agent.yaml
  - [root -> temperature]: Field temperature must be a Float between 0.0 and 1.0.
```

### Export JSON Schemas

The `export` command generates standard JSON Schema files for all core models. This is useful for frontend integration (e.g., generating forms).

```bash
poetry run coreason-val export ./schemas_out
```

This will create files like `agent.schema.json`, `bec.schema.json`, etc., in the specified directory.

## Python API Usage

For deep integration, import `coreason_validator` directly.

### Validation

#### Validate a File Path

The `validate_file` function handles file reading, parsing, schema inference, and validation.

```python
from coreason_validator.validator import validate_file

result = validate_file("path/to/agent.yaml")

if result.is_valid:
    print("Valid!")
    model = result.model
    print(f"Loaded model: {model}")
else:
    print("Invalid!")
    for error in result.errors:
        print(error)
```

#### Validate a Dictionary (Runtime)

Use `validate_object` to check in-memory dictionaries. This is optimized for low latency.

```python
from coreason_validator.validator import validate_object

data = {
    "name": "my-agent",
    "version": "1.0.0",
    # ... other fields
}

try:
    # Validate against 'agent' schema alias or the class directly
    agent = validate_object(data, "agent")
    print(f"Agent validated: {agent.name}")
except ValueError as e:
    print(f"Validation failed: {e}")
```

### Compliance Checking

Use `check_compliance` to verify that an output matches an expected JSON schema structure. This is often used in testing/grading (Assay).

```python
from coreason_validator.validator import check_compliance

agent_output = {"summary": "This is a summary."}
expected_schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"}
    },
    "required": ["summary"]
}

try:
    check_compliance(agent_output, expected_schema)
    print("Compliance check passed.")
except ValueError as e:
    print(f"Compliance check failed: {e}")
```

### Canonical Hashing

Use `canonical_hash` to generate a consistent hash of the model's content, ignoring whitespace and key order.

```python
from coreason_validator.validator import validate_object

data = {"key": "value", "a": 1}
model = validate_object(data, "some_schema") # Replace with actual schema

hash_val = model.canonical_hash()
print(f"Canonical Hash: {hash_val}")
```

### Sanitization

The `sanitize_inputs` utility strips dangerous characters (like null bytes) and trims whitespace. It is automatically called by `validate_object`.

```python
from coreason_validator.validator import sanitize_inputs

raw_data = {"name": "  my-agent  \0 "}
clean_data = sanitize_inputs(raw_data)
# clean_data is {"name": "my-agent"}
```
