from typing import Literal

from pydantic import BaseModel, Field, constr


class AgentManifest(BaseModel):
    """
    Defines the configuration for a CoReason Agent.
    """

    schema_version: Literal["1.0"] = "1.0"
    name: constr(pattern=r"^[a-z0-9-]+$") = Field(  # type: ignore
        ..., description="Kebab-case strict name"
    )
    version: constr(pattern=r"^\d+\.\d+\.\d+$") = Field(  # type: ignore
        ..., description="SemVer strict version"
    )
    model_config_id: str = Field(
        ...,
        alias="model_config",
        description="Must match allowlist in Manifest",
        min_length=1,
    )
    max_cost_limit: float = Field(gt=0.0, description="Maximum cost limit in dollars")
