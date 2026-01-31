# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import json
from pathlib import Path

from coreason_validator.validator import validate_file


def test_ambiguous_inference(tmp_path: Path) -> None:
    """Test inference when file matches multiple schemas."""
    # AgentDefinition checks 'interface' and 'metadata'.
    # RecipeManifest checks 'graph' and 'inputs'.
    # Create file with both sets of keys.
    data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "ambiguous",
            "author": "tester",
            "created_at": "2025-01-01T00:00:00Z",
        },
        "interface": {},
        # Recipe fields
        "graph": {"nodes": [], "edges": []},
        "inputs": {},
        # Agent required fields to make it "almost" valid agent if chosen
        "topology": {"steps": [{"id": "s1"}], "model_config": {"model": "gpt-4", "temperature": 0.7}},
        "dependencies": {},
        "integrity_hash": "a" * 64,
        # Recipe required fields
        # RecipeManifest also requires id, version, name, description.
        # id, version, name are in metadata for Agent, but top-level for Recipe.
        "id": "recipe1",
        "version": "1.0.0",
        "name": "recipe",
    }
    p = tmp_path / "ambiguous.json"
    p.write_text(json.dumps(data))

    # The registry order matters.
    # Agent is checked first?
    # Registry implementation uses a dict. In Python 3.7+ insertion order is preserved.
    # I registered 'agent' first, then 'bec' (Recipe).
    # So it should infer AgentDefinition.

    # Since 'extra="forbid"' is strictly enforced in AgentDefinition,
    # validation will fail due to presence of 'graph', 'inputs', 'id' (top-level), 'name' (top-level).

    result = validate_file(p)
    assert not result.is_valid

    # It should complain about extra fields.
    err_str = str(result.errors)
    assert "extra_forbidden" in err_str or "Extra inputs" in err_str
