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
from coreason_validator.schemas.topology import TopologyGraph, TopologyNode
from pydantic import ValidationError


def test_topology_valid_linear() -> None:
    """
    Test a simple valid linear graph: A -> B -> C
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B"]),
        TopologyNode(id="B", step_type="process", next_steps=["C"]),
        TopologyNode(id="C", step_type="end", next_steps=[]),
    ]
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == 3
    assert graph.nodes[0].id == "A"


def test_topology_valid_branching() -> None:
    """
    Test a valid branching graph:
      /-> B
    A
      \\-> C
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B", "C"]),
        TopologyNode(id="B", step_type="process", next_steps=[]),
        TopologyNode(id="C", step_type="process", next_steps=[]),
    ]
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == 3


def test_topology_duplicate_ids() -> None:
    """
    Test that duplicate node IDs raise a ValueError.
    """
    nodes = [
        TopologyNode(id="A", step_type="start"),
        TopologyNode(id="A", step_type="end"),
    ]
    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)
    assert "Duplicate node ID found: 'A'" in str(exc.value)


def test_topology_missing_reference() -> None:
    """
    Test that pointing to a non-existent node raises a ValueError.
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B"]),
    ]
    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)
    assert "Node 'A' points to non-existent node ID: 'B'" in str(exc.value)


def test_topology_cycle_self_loop() -> None:
    """
    Test that a self-loop (A -> A) raises a ValueError.
    """
    nodes = [
        TopologyNode(id="A", step_type="loop", next_steps=["A"]),
    ]
    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)
    assert "Cycle detected in topology: A -> A" in str(exc.value)


def test_topology_cycle_complex() -> None:
    """
    Test a larger cycle: A -> B -> C -> A
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B"]),
        TopologyNode(id="B", step_type="process", next_steps=["C"]),
        TopologyNode(id="C", step_type="end", next_steps=["A"]),
    ]
    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)
    # The error message should show the path
    assert "Cycle detected in topology: A -> B -> C -> A" in str(exc.value)


def test_topology_cycle_disconnected_component() -> None:
    """
    Test that cycles are detected even in disconnected components.
    Graph:
    A -> B (Valid)
    C -> D -> C (Cycle)
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B"]),
        TopologyNode(id="B", step_type="end", next_steps=[]),
        TopologyNode(id="C", step_type="loop", next_steps=["D"]),
        TopologyNode(id="D", step_type="loop", next_steps=["C"]),
    ]
    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=nodes)
    assert "Cycle detected in topology: C -> D -> C" in str(exc.value)


def test_topology_empty_graph() -> None:
    """
    Test that an empty graph is invalid (min_length=1).
    """
    with pytest.raises(ValidationError) as exc:
        TopologyGraph(nodes=[])
    assert "List should have at least 1 item" in str(exc.value)


def test_topology_canonical_hash() -> None:
    """
    Test that TopologyGraph inherits canonical_hash correctly.
    """
    nodes = [
        TopologyNode(id="A", step_type="start"),
    ]
    graph = TopologyGraph(nodes=nodes)
    hash_val = graph.canonical_hash()
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA-256 hex digest length


def test_topology_valid_diamond() -> None:
    """
    Test a diamond pattern:
      /-> B -\
    A         -> D
      \\-> C -/
    This checks that visiting D via B doesn't mark it as 'visiting' (cycle)
    when we later try to reach it via C. It should be 'visited'.
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B", "C"]),
        TopologyNode(id="B", step_type="process", next_steps=["D"]),
        TopologyNode(id="C", step_type="process", next_steps=["D"]),
        TopologyNode(id="D", step_type="end", next_steps=[]),
    ]
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == 4


def test_topology_valid_disconnected() -> None:
    """
    Test multiple disconnected valid components.
    A -> B
    C -> D
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B"]),
        TopologyNode(id="B", step_type="end", next_steps=[]),
        TopologyNode(id="C", step_type="start", next_steps=["D"]),
        TopologyNode(id="D", step_type="end", next_steps=[]),
    ]
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == 4


def test_topology_redundant_edges() -> None:
    """
    Test that duplicate edges (A points to B twice) are handled gracefully
    and don't cause cycles or errors.
    """
    nodes = [
        TopologyNode(id="A", step_type="start", next_steps=["B", "B"]),
        TopologyNode(id="B", step_type="end", next_steps=[]),
    ]
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == 2


def test_topology_complex_config() -> None:
    """
    Test that the 'config' field handles complex nested dictionaries.
    """
    config_data = {
        "model": "gpt-4",
        "params": {"temperature": 0.7, "stops": ["\n"]},
        "retry": True,
    }
    nodes = [
        TopologyNode(id="A", step_type="llm", config=config_data),
    ]
    graph = TopologyGraph(nodes=nodes)
    assert graph.nodes[0].config == config_data

    # Ensure hashing works with nested dicts
    hash_val = graph.canonical_hash()
    assert isinstance(hash_val, str)


def test_topology_large_chain() -> None:
    """
    Test a long chain of nodes to verify recursion/performance.
    0 -> 1 -> 2 -> ... -> 99
    """
    chain_length = 100
    nodes = []
    for i in range(chain_length):
        next_steps = [str(i + 1)] if i < chain_length - 1 else []
        nodes.append(TopologyNode(id=str(i), step_type="step", next_steps=next_steps))

    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == chain_length


def test_topology_deep_recursion_limit() -> None:
    """
    Test a chain deep enough to trigger RecursionError in recursive implementations.
    Standard Python recursion limit is 1000. We test with 2000.
    """
    chain_length = 2000
    nodes = []
    for i in range(chain_length):
        next_steps = [str(i + 1)] if i < chain_length - 1 else []
        nodes.append(TopologyNode(id=str(i), step_type="step", next_steps=next_steps))

    # Should not raise RecursionError or ValidationError
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == chain_length
