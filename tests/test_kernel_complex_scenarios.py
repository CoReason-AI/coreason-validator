# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.recipes import RecipeManifest

from coreason_validator.validator import validate_object

# Constants
VALID_SHA256 = "a" * 64
VALID_UUID = str(uuid4())


def test_mega_recipe_complex_topology() -> None:
    """
    Test a 'Mega Recipe' containing a complex GraphTopology with various node types and conditional edges.
    """
    recipe_data: Dict[str, Any] = {
        "id": "recipe-mega",
        "version": "1.0.0",
        "name": "Mega Orchestrator",
        "description": "Complex workflow",
        "interface": {
            "inputs": {"type": "object", "properties": {"query": {"type": "string"}}},
            "outputs": {"type": "object", "properties": {"result": {"type": "string"}}},
        },
        "state": {
            "schema": {"type": "object"},
            "persistence": "persistent",
        },
        "parameters": {"max_retries": 3},
        "topology": {
            "nodes": [
                # Node 1: Agent
                {
                    "type": "agent",
                    "id": "research_agent",
                    "agent_name": "researcher-v1",
                    "visual": {"label": "Research Phase", "x_y_coordinates": [0.0, 0.0]},
                },
                # Node 2: Human Interaction
                {
                    "type": "human",
                    "id": "human_review",
                    "timeout_seconds": 3600,
                    "council_config": {"strategy": "majority", "voters": ["admin", "supervisor"]},
                },
                # Node 3: Python Logic
                {
                    "type": "logic",
                    "id": "format_data",
                    "code": "def run(state): return {'data': str(state)}",
                },
                # Node 4: Map (Parallel Processing)
                {
                    "type": "map",
                    "id": "process_items",
                    "items_path": "data.items",
                    "processor_node_id": "process_single_item",
                    "concurrency_limit": 5,
                },
            ],
            "edges": [
                # Standard Edge
                {"source_node_id": "research_agent", "target_node_id": "human_review"},
                # Conditional Edge with Router Logic
                {
                    "source_node_id": "human_review",
                    "router_logic": {
                        "operator": "eq",
                        "args": [{"var": "review_status"}, "approved"],
                    },
                    "mapping": {
                        "true": "format_data",
                        "false": "research_agent",  # Loop back
                    },
                },
            ],
            "state_schema": {
                "data_schema": {"type": "object"},
                "persistence": "redis",
            },
        },
    }

    # Validate
    recipe = validate_object(recipe_data, RecipeManifest)

    assert recipe.id == "recipe-mega"
    assert len(recipe.topology.nodes) == 4
    # Check polymorphism
    nodes_by_id = {n.id: n for n in recipe.topology.nodes}
    assert nodes_by_id["research_agent"].type == "agent"
    assert nodes_by_id["human_review"].type == "human"
    assert nodes_by_id["format_data"].type == "logic"

    # Check conditional edge
    edges = recipe.topology.edges
    assert len(edges) == 2
    # Find conditional edge
    cond_edge = next(e for e in edges if hasattr(e, "router_logic"))
    assert cond_edge.source_node_id == "human_review"
    assert cond_edge.mapping["true"] == "format_data"


def test_secure_agent_full_config() -> None:
    """
    Test a 'Secure Agent' with comprehensive configuration including policy, dependencies, and observability.
    """
    agent_data: Dict[str, Any] = {
        "metadata": {
            "id": VALID_UUID,
            "version": "2.5.0",
            "name": "finance-analyst",
            "author": "sec-team",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "requires_auth": True,
        },
        "interface": {
            "inputs": {"type": "object"},
            "outputs": {"type": "object"},
            # Must include user_context because requires_auth is True
            "injected_params": ["user_context", "trace_id"],
        },
        "config": {
            "nodes": [{"type": "agent", "id": "entry", "agent_name": "core"}],
            "edges": [],
            "entry_point": "entry",
            "model_config": {"model": "claude-3-opus", "temperature": 0.1},
        },
        "dependencies": {
            "tools": [
                {
                    "uri": "https://mcp.coreason.ai/tools/calculator",
                    "hash": "b" * 64,  # Fake hash
                    "scopes": ["math:read", "math:calc"],
                    "risk_level": "safe",
                },
                {
                    "uri": "https://mcp.coreason.ai/tools/db-access",
                    "hash": "c" * 64,
                    "scopes": ["db:read_only"],
                    "risk_level": "critical",
                },
            ],
            "libraries": ["pandas", "numpy"],
        },
        "policy": {
            "budget_caps": {
                "total_cost_usd": 50.0,
                "max_tokens_per_run": 100000,
            },
            "human_in_the_loop": ["db-access-node"],
            "allowed_domains": ["coreason.ai", "finance.data.gov"],
        },
        "observability": {
            "trace_level": "full",
            "retention_policy": "90_days_encrypted",
            "encryption_key_id": "kms-key-123",
        },
        "integrity_hash": VALID_SHA256,
    }

    agent = validate_object(agent_data, AgentDefinition)

    # Verification
    assert agent.metadata.name == "finance-analyst"
    assert agent.policy is not None
    assert agent.policy.budget_caps["total_cost_usd"] == 50.0
    assert "coreason.ai" in agent.policy.allowed_domains

    assert agent.dependencies.tools[0].risk_level == "safe"
    assert agent.dependencies.tools[1].risk_level == "critical"

    assert agent.observability.trace_level == "full"
    assert agent.observability.encryption_key_id == "kms-key-123"
