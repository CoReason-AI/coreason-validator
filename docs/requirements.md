# **Product Requirements Document: coreason-validator**

Domain: Structural Conformance, Schema Validation, & Data Integrity
Architectural Role: The "Building Inspector" & Universal Schema Registry
Core Philosophy: "Trust, but Validate. Fail Fast, Fail Loud."
Dependencies: pydantic>=2.0 (Core Logic), jsonschema (Interoperability)

## ---

**1\. Executive Summary**

coreason-validator is the foundational library responsible for enforcing structural integrity across the entire CoReason ecosystem. It acts as the **Single Source of Truth** for all data structures (Agents, Tests, Topologies, Messages).

In a GxP environment, "Implicit Trust" is a vulnerability. Component A must never assume Component B sent valid data. coreason-validator provides the "Schemas-as-Code" definitions and the validation logic to check assets *before* they are processed. Unlike coreason-veritas (which records what happened), coreason-validator ensures that what *is about to happen* is structurally sound.

## **2\. Functional Philosophy**

The agent must implement the **Define-Check-Hash Loop**:

1. **Schemas as Code:** Validation rules are not loose JSON files; they are strict Python classes (Pydantic V2). This allows for inheritance, complex validation logic (e.g., "Field A is required only if Field B is True"), and IDE autocompletion.
2. **Shift-Left Validation:** Validation should happen as early as possible. An SRE should catch a configuration error on their laptop (via CLI), not inside the production cluster.
3. **Universal Language:** The same schema definition used to validate an API payload in Python must be exported (as JSON Schema) to generate the Form UI in React. This prevents Frontend/Backend drift.
4. **The GxP Seal:** The library provides canonical hashing. To prove file integrity, we don't just hash the bytes; we hash the *validated structure*, ensuring whitespace changes don't break the seal.

## ---

**3\. Core Functional Requirements (Component Level)**

### **3.1 The Schema Registry (The Law)**

**Concept:** A collection of immutable Pydantic Models defining valid assets.

* **AgentManifest:** Defines agent.yaml.
  * *Rules:* SemVer strictness, allowed Model IDs (Enums), required Topology pointers.
* **TopologyGraph:** Defines the Node/Edge structure.
  * *Rules:* Must be a Directed Acyclic Graph (DAG). Validates that next\_step pointers refer to existing Node IDs.
* **BECManifest:** Defines the Benchmark Evaluation Corpus.
  * *Rules:* Enforces input vs expected\_output structure. Validates that expected\_structure is a valid JSON Schema string.
* **ToolCallPayload:** Defines the strict inputs for coreason-mcp.
  * *Rules:* Type strictness (Ints are Ints, not Strings). SQL Injection pattern matching on string inputs.

### **3.2 The Static Analyzer (The Linter)**

**Concept:** A validation engine that runs on static files.

* **validate\_file(path, schema\_type):** Reads a file (JSON/YAML), detects the schema type, and validates.
* **Error Reporting:** Returns *Rich Diagnostics*, not just "Invalid JSON."
  * *Example:* "Error in agent.yaml: Node 'ResearchStep' is missing required output field 'summary'."

### **3.3 The Runtime Guard (The Shield)**

**Concept:** A lightweight validation function for dynamic payloads.

* **validate\_object(dict, schema\_type):** Used by MACO/MCP to check in-memory objects (microseconds latency).
* **sanitize\_inputs(dict):** Automatically strips dangerous characters or trims whitespace before validation passes.

### **3.4 The Integrity Hasher (The Seal)**

**Concept:** Ensures strict consistency for the Publisher.

* **canonical\_hash(model):**
  1. Validates the object.
  2. Sorts all keys alphabetically.
  3. Removes non-semantic whitespace.
  4. Returns SHA-256.
* **Usage:** This hash is what gets signed by the SRB in coreason-publisher.

### **3.5 The Frontend Bridge (The Exporter)**

**Concept:** Ensures the UI matches the Backend.

* **export\_json\_schema(output\_dir):** A utility that serializes all Pydantic models into standard schema.json files.
* **Usage:** The CI/CD pipeline runs this, and the React Frontend consumes these JSON files to auto-generate form validation rules.

## ---

**4\. Integration Requirements (The Ecosystem)**

### **4.1 Foundry (The Gatekeeper)**

* **Ingestion:** When an SRE uploads a draft, Foundry calls validator.validate\_file(). If it fails, the upload is rejected with a distinct error message.
* **UI Generation:** Foundry uses the *Schema* to dynamically render the "Agent Config" form.

### **4.2 MCP (The Tool Shield)**

* **Pre-Execution:** Before executing any Tool (e.g., SQL Query), MCP calls validator.validate\_tool\_call().
* **Benefit:** Prevents the LLM from hallucinating arguments that would crash the tool driver.

### **4.3 Assay (The Grader)**

* **Output Checking:** Assay uses validator to check if the *Agent's actual response* adheres to the expected\_structure defined in the BEC.
* **Logic:** validator.check\_compliance(agent\_output\_json, target\_schema\_json).

### **4.4 Publisher (The Auditor)**

* **Integrity:** Publisher calls validator.canonical\_hash() on every file in the bundle to generate the Manifest for the CoA.

### **4.5 MACO (The Protocol)**

* **Message Passing:** When Agent A sends a message to Agent B (Council Mode), MACO calls validator.validate\_message(). If invalid, it triggers a "Self-Correction" prompt to Agent A.

## ---

**5\. User Stories (Behavioral Expectations)**

### **Story A: The "Local Lint" (Shift Left)**

Trigger: SRE is editing agent.yaml locally and types temperature: "high".
Action: SRE runs coreason-validator check .
Result: Tool fails: "Error at agent.yaml: Field temperature must be a Float between 0.0 and 1.0."
Value: SRE fixes the bug before wasting time uploading to Foundry.

### **Story B: The "Malicious Hallucination" (MCP Safety)**

Trigger: An Agent hallucinates a tool call to patient\_db: { "limit": "DROP TABLE users" }.
Action: MCP receives payload. Calls validator.validate\_tool\_call().
Result: Validation Fails. "Field limit expects Integer, got String."
Outcome: The SQL Injection is blocked. The Agent is sent an error message: "Invalid Tool Argument."

### **Story C: The "Frontend Sync" (DRY)**

Trigger: Backend Architect adds a new field max\_retries to the AgentManifest in coreason-validator.
Action: CI Pipeline runs export\_json\_schema.
Result: The React UI library pulls the new schema. The "Agent Settings" page automatically displays a new Input Box for "Max Retries" with number validation. No frontend code changes required.

## ---

**6\. Data Schema Examples (Implementation Guide)**

Python

from pydantic import BaseModel, Field, constr
from typing import List, Literal, Optional

\# 1\. The Agent Manifest (Config)
class AgentManifest(BaseModel):
    schema\_version: Literal\["1.0"\] \= "1.0"
    name: constr(pattern=r"^\[a-z0-9-\]+$") \# Kebab-case strict
    version: constr(pattern=r"^\\d+\\.\\d+\\.\\d+$") \# SemVer strict
    model\_config: str \= Field(..., description="Must match allowlist in Manifest")
    max\_cost\_limit: float \= Field(gt=0.0)

\# 2\. The Benchmark Corpus (Test Data)
class TestCase(BaseModel):
    id: str
    prompt: str
    context\_files: List\[str\]
    expected\_output\_structure: Optional\[dict\] \# JSON Schema dict

class BECManifest(BaseModel):
    corpus\_id: str
    cases: List\[TestCase\]

\# 3\. The Tool Call (Runtime Safety)
class ToolCall(BaseModel):
    tool\_name: str
    arguments: dict

## ---

**7\. Implementation Directives for the Coding Agent**

1. **Pydantic V2:** Use Pydantic V2 strictly for the Rust-based serialization speed. This package will be called thousands of times per minute in the runtime.
2. **Zero Dependencies:** Do not import coreason-cortex or coreason-foundry into this package. validator is the *base* dependency.
3. **CLI Entrypoint:** Expose a CLI command coreason-val that accepts a file path.
4. **Error Formatting:** Do not return Python Tracebacks to the user. Catch ValidationError, parse the loc (location) tuple, and print a human-readable string: "Field 'x' is missing."
5. **Schema Versioning:** Every Schema class must have a schema\_version field. If Foundry receives a file with schema\_version="0.9", it should know to migrate or reject it.
