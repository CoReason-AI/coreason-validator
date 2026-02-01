# CoReason Manifest Integration

This document outlines how `coreason-validator` integrates with the `coreason-manifest` Shared Kernel to enforce strict structural integrity across the ecosystem.

## Overview

The `coreason-validator` no longer maintains its own Pydantic schema definitions. Instead, it serves as a strict enforcement layer for the canonical models defined in the [coreason-manifest](https://github.com/CoReason-AI/coreason-manifest) library.

This architecture ensures a **Single Source of Truth** for all artifact definitions (Agents, Recipes, Topologies, etc.).

## Key Kernel Classes

The Validator maps internal string aliases to the following Kernel classes:

| Alias | Kernel Class | Import Path | Description |
| :--- | :--- | :--- | :--- |
| `agent` | `AgentDefinition` | `coreason_manifest.definitions.agent` | Defines an atomic Agent, including its metadata, interface, config, and integrity hash. |
| `recipe` | `RecipeManifest` | `coreason_manifest.recipes` | Defines a composite workflow (Recipe) orchestration. |
| `topology` | `GraphTopology` | `coreason_manifest.definitions.topology` | Defines the graph structure (Nodes and Edges) used within Agents and Recipes. |
| `tool` | `ToolCallRequestPart` | `coreason_manifest.definitions.message` | Defines the structure of a tool call request from an LLM. |
| `message` | `Message` | `coreason_manifest.definitions.message` | Defines the standard ChatMessage structure (User/Assistant/System roles). |
| `audit` | `AuditLog` | `coreason_manifest.definitions.audit` | Defines the tamper-evident audit record structure. |

## Structural Requirements

### AgentDefinition
The `AgentDefinition` is stricter than previous versions. Key requirements include:

1.  **Integrity Hash:** A top-level `integrity_hash` field is **mandatory**. It must be a valid SHA256 hex string (64 characters).
2.  **Metadata Nesting:** Identifying fields (`id`, `version`, `name`) are now nested under a `metadata` object.
3.  **Strict SemVer:** The `version` field must adhere to Semantic Versioning.
4.  **Auth Validation:** If `metadata.requires_auth` is `True`, the `interface.injected_params` list **must** contain `"user_context"`.

### GraphTopology
The topology supports polymorphic nodes via a discriminated union. The `type` field determines the validation schema for each node:

*   `type: "agent"` -> `AgentNode`
*   `type: "human"` -> `HumanNode`
*   `type: "logic"` -> `LogicNode`
*   `type: "map"` -> `MapNode`
*   `type: "recipe"` -> `RecipeNode`

### RecipeManifest
Replaces the legacy `BECManifest`. It requires:
*   `interface`: Input/Output JSON schemas.
*   `topology`: The execution graph.
*   `state`: Definition of shared memory persistence.

## Validation Process

1.  **Sanitization:** Inputs are recursively sanitized (whitespace trimmed, null bytes stripped).
2.  **Inference:** If no schema type is provided, the Validator attempts to infer it based on unique keys:
    *   `integrity_hash` + `config` -> `AgentDefinition`
    *   `topology` + `interface` -> `RecipeManifest`
    *   `nodes` + `edges` + `state_schema` -> `GraphTopology`
3.  **Strict Parsing:** The input is validated against the Pydantic model. Extra fields are generally forbidden (`model_config['extra'] = 'forbid'`).
4.  **Result:** A `ValidationResult` object is returned, containing the parsed model or structured error messages.

## Usage Example

```python
from coreason_validator.validator import validate_file, AgentDefinition

# Validate a file explicitly as an Agent
result = validate_file("path/to/agent.json", AgentDefinition)

if result.is_valid:
    agent = result.model # Type: AgentDefinition
    print(f"Validated Agent: {agent.metadata.name}")
else:
    print("Validation Errors:", result.errors)
```
