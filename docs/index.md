# Welcome to coreason-validator

**coreason-validator** is the foundational library responsible for enforcing structural integrity across the entire CoReason ecosystem. It acts as the **Single Source of Truth** for all data structures (Agents, Tests, Topologies, Messages).

## Key Features

*   **Schema Registry**: A collection of immutable Pydantic Models defining valid assets.
*   **Static Analyzer**: A validation engine that runs on static files (JSON/YAML) with rich error reporting.
*   **Runtime Guard**: A lightweight validation function for dynamic payloads with microsecond latency.
*   **Integrity Hasher**: Provides canonical hashing to ensure file integrity and GxP compliance.
*   **Frontend Bridge**: Exports JSON Schemas to keep the UI in sync with the backend.

## Documentation

*   [Usage Guide](usage.md): Learn how to use the CLI and Python API.
*   [Architecture](architecture.md): Understand the core philosophy and components.
*   [Requirements](requirements.md): View the original Product Requirements Document.
