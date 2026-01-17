# Architecture

`coreason-validator` is the foundational library for enforcing structural integrity across the CoReason ecosystem. It acts as the "Building Inspector" and "Universal Schema Registry", ensuring that all data structures (Agents, Tests, Topologies, Messages) adhere to strict standards.

## Core Philosophy: The Define-Check-Hash Loop

The library enforces a rigorous lifecycle for all data assets:

1.  **Define (Schemas as Code)**: Validation rules are defined as strict Python classes using Pydantic V2. This enables inheritance, complex logic, and IDE support.
2.  **Check (Shift-Left Validation)**: Validation occurs as early as possible—locally via CLI or at the API gateway—preventing invalid data from entering the production cluster.
3.  **Hash (The GxP Seal)**: Integrity is proven by hashing the *validated structure*, not just the raw bytes. This ensures semantic consistency even if whitespace changes.

## Components

The library is composed of five key architectural components:

### 1. The Schema Registry (The Law)
A collection of immutable Pydantic Models that define valid assets.
*   **AgentManifest**: Defines `agent.yaml` (SemVer, Model IDs, Topology pointers).
*   **TopologyGraph**: Defines Node/Edge structures (DAG validation).
*   **BECManifest**: Defines the Benchmark Evaluation Corpus (Input vs Expected Output).
*   **ToolCallPayload**: Defines strict inputs for tool execution (Type strictness, SQL injection patterns).

### 2. The Static Analyzer (The Linter)
A validation engine for static files.
*   **Function**: `validate_file(path, schema_type)`
*   **Role**: Reads JSON/YAML files, detects schema types, and provides rich error diagnostics (e.g., specific missing fields or type mismatches).

### 3. The Runtime Guard (The Shield)
A lightweight validation engine for dynamic, in-memory payloads.
*   **Function**: `validate_object(dict, schema_type)`
*   **Role**: Used by services like MACO and MCP to check objects with microsecond latency.
*   **Sanitization**: Automatically strips dangerous characters and trims whitespace via `sanitize_inputs`.

### 4. The Integrity Hasher (The Seal)
Ensures strict consistency for auditing.
*   **Function**: `canonical_hash(model)`
*   **Role**:
    1.  Validates the object.
    2.  Sorts keys alphabetically.
    3.  Removes non-semantic whitespace.
    4.  Generates a SHA-256 hash.
    *   This hash is signed by the Publisher to create the Chain of Custody.

### 5. The Frontend Bridge (The Exporter)
Ensures the UI stays in sync with the Backend.
*   **Function**: `export_json_schema(output_dir)`
*   **Role**: Serializes Pydantic models into standard JSON Schema files. These are consumed by the Frontend to auto-generate form validation rules, preventing drift.

## Integration Ecosystem

`coreason-validator` is integrated into every stage of the lifecycle:

*   **Foundry (The Gatekeeper)**: Rejects invalid agent drafts upon ingestion and uses schemas to generate UI forms.
*   **MCP (The Tool Shield)**: Validates tool arguments before execution to prevent LLM hallucinations (e.g., SQL injection).
*   **Assay (The Grader)**: Checks if an agent's response complies with the expected structure defined in the benchmark corpus.
*   **Publisher (The Auditor)**: Generates canonical hashes for every file in a bundle to ensure integrity.
*   **MACO (The Protocol)**: Validates inter-agent messages and triggers self-correction prompts if validation fails.
