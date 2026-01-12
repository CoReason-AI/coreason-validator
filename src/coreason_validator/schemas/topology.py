# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


from typing import Any, Dict, List, Literal, Optional

from pydantic import ConfigDict, Field, model_validator

from coreason_validator.schemas.base import CoReasonBaseModel


class TopologyNode(CoReasonBaseModel):
    """
    Represents a single node in the topology graph.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1, description="Unique identifier for the node")
    step_type: str = Field(..., min_length=1, description="Type of the step (e.g., 'prompt', 'tool')")
    next_steps: List[str] = Field(default_factory=list, description="List of downstream node IDs")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Step-specific configuration")


class TopologyGraph(CoReasonBaseModel):
    """
    Defines the Node/Edge structure for an agent's workflow.
    Enforces DAG structure (no cycles) and referential integrity.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    nodes: List[TopologyNode] = Field(..., min_length=1, description="List of nodes in the graph")

    @model_validator(mode="after")
    def validate_graph_integrity(self) -> "TopologyGraph":
        """
        Validates:
        1. All next_step pointers refer to existing Node IDs.
        2. The graph contains no cycles (is a DAG).
        """
        # 1. Build a map of ID -> Node and check for duplicate IDs
        node_map: Dict[str, TopologyNode] = {}
        for node in self.nodes:
            if node.id in node_map:
                raise ValueError(f"Duplicate node ID found: '{node.id}'")
            node_map[node.id] = node

        # 2. Validate referential integrity
        for node in self.nodes:
            for next_id in node.next_steps:
                if next_id not in node_map:
                    raise ValueError(f"Node '{node.id}' points to non-existent node ID: '{next_id}'")

        # 3. Cycle Detection (Custom DFS)
        # States: 0 = unvisited, 1 = visiting (recursion stack), 2 = visited
        visited: Dict[str, int] = {node.id: 0 for node in self.nodes}

        def dfs(current_id: str, path: List[str]) -> None:
            visited[current_id] = 1  # Mark as visiting
            path.append(current_id)

            current_node = node_map[current_id]
            for neighbor_id in current_node.next_steps:
                if visited[neighbor_id] == 1:
                    # Cycle detected
                    try:
                        start_index = path.index(neighbor_id)
                        cycle_path = path[start_index:] + [neighbor_id]
                        cycle_str = " -> ".join(cycle_path)
                    except ValueError:  # pragma: no cover
                        cycle_str = f"Unknown cycle involving {neighbor_id}"

                    raise ValueError(f"Cycle detected in topology: {cycle_str}")

                if visited[neighbor_id] == 0:
                    dfs(neighbor_id, path)

            path.pop()
            visited[current_id] = 2  # Mark as fully visited

        for node in self.nodes:
            if visited[node.id] == 0:
                dfs(node.id, [])

        return self
