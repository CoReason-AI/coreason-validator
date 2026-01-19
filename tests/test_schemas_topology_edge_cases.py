# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

import pytest
from pydantic import ValidationError

from coreason_validator.schemas.topology import TopologyGraph, TopologyNode


def test_topology_deep_cycle() -> None:
    """
    Test a deep cycle: 0 -> 1 -> ... -> 1999 -> 1000
    This creates a loop of length 1000 at the end of a 1000-node chain.
    Verifies that the iterative DFS correctly identifies cycles deep in the graph.
    """
    chain_length = 2000
    loop_back_to = 1000
    nodes = []
    for i in range(chain_length):
        # Last node points back to loop_back_to
        if i == chain_length - 1:
            next_steps = [str(loop_back_to)]
        else:
            next_steps = [str(i + 1)]

        nodes.append(TopologyNode(id=str(i), step_type="step", next_steps=next_steps))

    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)

    # Verify the cycle is detected and the path string contains the loop
    # The path should end with ... -> 1999 -> 1000
    err_msg = str(exc.value)
    assert "Cycle detected in topology" in err_msg
    # We expect "1000 -> 1001 -> ... -> 1999 -> 1000"
    # Checking for a segment is sufficient
    assert f"{loop_back_to} -> {loop_back_to + 1}" in err_msg
    assert f"{chain_length - 1} -> {loop_back_to}" in err_msg


def test_topology_star_graph() -> None:
    """
    Test a star graph: Root -> [Leaf1, Leaf2, ..., Leaf1000]
    Stress tests the neighbor iteration logic in the stack.
    """
    leaf_count = 1000
    leaves = [TopologyNode(id=f"Leaf{i}", step_type="end") for i in range(leaf_count)]
    leaf_ids = [n.id for n in leaves]

    root = TopologyNode(id="Root", step_type="start", next_steps=leaf_ids)

    nodes = [root] + leaves

    # Should be valid
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == leaf_count + 1


def test_topology_deep_self_loop() -> None:
    """
    Test a deep chain ending in a self-loop: 0 -> ... -> 1999 -> 1999
    """
    chain_length = 2000
    nodes = []
    for i in range(chain_length):
        # Last node points to itself
        if i == chain_length - 1:
            next_steps = [str(i)]
        else:
            next_steps = [str(i + 1)]

        nodes.append(TopologyNode(id=str(i), step_type="step", next_steps=next_steps))

    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)

    assert f"Cycle detected in topology: {chain_length - 1} -> {chain_length - 1}" in str(exc.value)


def test_topology_multiple_deep_components() -> None:
    """
    Test multiple disconnected deep chains to ensure 'visited' state is managed correctly
    across the outer loop of the DFS validator.
    Chain A: 0..999
    Chain B: 1000..1999
    """
    nodes = []
    # Chain A
    for i in range(1000):
        next_steps = [str(i + 1)] if i < 999 else []
        nodes.append(TopologyNode(id=str(i), step_type="step", next_steps=next_steps))

    # Chain B
    for i in range(1000, 2000):
        next_steps = [str(i + 1)] if i < 1999 else []
        nodes.append(TopologyNode(id=str(i), step_type="step", next_steps=next_steps))

    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == 2000


def test_topology_cycle_in_second_component() -> None:
    """
    Test disconnected components where the second one has a cycle.
    Chain A: 0 -> 1 (Valid)
    Chain B: 2 -> 3 -> 2 (Cycle)
    """
    nodes = [
        TopologyNode(id="0", step_type="start", next_steps=["1"]),
        TopologyNode(id="1", step_type="end", next_steps=[]),
        TopologyNode(id="2", step_type="start", next_steps=["3"]),
        TopologyNode(id="3", step_type="process", next_steps=["2"]),
    ]
    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)
    assert "Cycle detected in topology: 2 -> 3 -> 2" in str(exc.value)


def test_topology_grid_dag() -> None:
    """
    Test a Grid DAG: 20x20 grid where edges go Right and Down.
    (x, y) -> (x+1, y) and (x, y+1)
    This creates many overlapping paths to the bottom-right node.
    Validates that the DFS doesn't explode exponentially (O(V+E)).
    """
    width, height = 20, 20
    nodes = []
    for x in range(width):
        for y in range(height):
            node_id = f"{x},{y}"
            next_steps = []
            if x < width - 1:
                next_steps.append(f"{x + 1},{y}")
            if y < height - 1:
                next_steps.append(f"{x},{y + 1}")

            nodes.append(TopologyNode(id=node_id, step_type="step", next_steps=next_steps))

    # Total nodes = 400. Total edges ~ 800.
    # Number of paths from (0,0) to (19,19) is C(38, 19) ~ 35 billion.
    # Recursive naive DFS without correct memoization would timeout.
    # Iterative DFS with visited set should be instant.
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == width * height
