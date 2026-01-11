import pytest
from pydantic import ValidationError

from coreason_validator.schemas.topology import TopologyGraph, TopologyNode


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
