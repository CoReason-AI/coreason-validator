# The Architecture and Utility of coreason-validator

### 1. The Philosophy (The Why)
Coreason-validator exists to solve the "Implicit Trust" vulnerability inherent in complex distributed systems, particularly those operating within GxP (Good Practice) regulated environments. In such high-stakes domains, assuming that Component A sends valid data to Component B is not just risky—it is negligent.

The author’s intent is clear: establish a "Single Source of Truth" for the entire CoReason ecosystem. Whether it is an Agent configuration, a Topology definition, or a Benchmark corpus, the structure must be defined once and enforced everywhere. The philosophy is "Trust, but Validate. Fail Fast, Fail Loud."

This package is not merely a library; it is the "Building Inspector." By shifting validation left—allowing SREs to catch configuration errors on their laptops via CLI before deployment—it prevents costly runtime failures. Furthermore, it bridges the gap between backend logic and frontend presentation. By treating "Schemas as Code," coreason-validator ensures that the React UI and the Python backend speak the same language, eliminating the drift that plagues disconnected architectures.

### 2. Under the Hood (The Dependencies & logic)
The engine of coreason-validator is built upon a carefully selected stack designed for performance and rigor:

*   **`pydantic` (>=2.0):** The heavy lifting is done by Pydantic V2. This choice is deliberate; V2’s Rust-based core provides the serialization speed necessary for a library that will be called thousands of times per minute in a live runtime. It transforms loose dictionaries into strict, type-safe Python objects.
*   **`jsonschema`:** While Pydantic handles internal logic, `jsonschema` provides the "Rosetta Stone" for interoperability, allowing the system to export validation rules to the frontend or other non-Python components.

The internal logic implements a "Define-Check-Hash Loop." At the heart of this is the `CoReasonBaseModel`. This base class does more than just validate fields; it acts as a seal of integrity. It implements a `canonical_hash` method that normalizes the data—sorting keys, removing non-semantic whitespace—before generating a SHA-256 signature. This ensures that any change in the structural definition breaks the seal, a critical feature for audit trails in regulated environments. The library also includes a static analyzer (`validate_file`) for build-time checks and a lightweight runtime guard (`validate_object`) for protecting dynamic payloads like tool calls.

### 3. In Practice (The How)
The power of coreason-validator lies in its ability to turn abstract rules into executable code.

**Defining the Law**
Validation rules are defined as strict Pydantic models. Notice the use of `Literal` for versioning and regex patterns for strict formatting. This is not just a hint; it is a contract.

```python
from typing import Literal
from pydantic import Field, constr
from coreason_validator.schemas.base import CoReasonBaseModel

class AgentManifest(CoReasonBaseModel):
    """
    Defines the strict configuration for a CoReason Agent.
    """
    schema_version: Literal["1.0"] = "1.0"
    name: constr(pattern=r"^[a-z0-9-]+$") = Field(..., description="Kebab-case strict name")
    version: constr(pattern=r"^\d+\.\d+\.\d+$") = Field(..., description="SemVer strict version")
    model_config_id: Literal["gpt-4-turbo", "claude-3-opus"] = Field(..., alias="model_config", description="Allowed model ID")
    max_cost_limit: float = Field(gt=0.0, description="Maximum cost limit in dollars")
    topology: str = Field(..., description="Path to the topology definition file")
```

**Enforcing the Law (The Linter)**
In practice, an SRE or a CI/CD pipeline uses the validator to check files before they ever reach the production environment. The `validate_file` function parses, infers the schema, and returns rich diagnostics.

```python
from coreason_validator.validator import validate_file

# The SRE runs this against their local config
result = validate_file("configs/agent.yaml", schema_type="agent")

if result.is_valid:
    print(f"✅ Valid Agent Config: {result.model.name}")
else:
    # Fail fast with specific errors
    for error in result.errors:
        print(f"❌ Error in {error['loc']}: {error['msg']}")
```

**Sealing the Deal (The Seal)**
Finally, to ensure integrity across the lifecycle, we generate a canonical hash. This hash proves that the validated structure has not been tampered with since validation.

```python
# Create an instance of the model
agent = AgentManifest(
    name="research-bot",
    version="1.0.0",
    model_config="gpt-4-turbo",
    max_cost_limit=50.0,
    topology="topologies/research_v1.yaml"
)

# Generate the GxP-compliant seal
integrity_hash = agent.canonical_hash()
print(f"🔐 Canonical Hash: {integrity_hash}")
# This hash can now be signed and stored in the manifest.
```
