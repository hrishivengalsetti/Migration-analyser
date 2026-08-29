import pytest
import networkx as nx
from brain.blast_radius import compute_blast_radius

def test_direct_caller_detected():
    G = nx.DiGraph()
    G.add_edge("A", "B")  # A calls/imports B

    res = compute_blast_radius(G, ["B"])
    assert res.directly_affected == ["A"]
    assert res.transitively_affected == []
    assert res.all_affected == ["A"]
    assert res.total_affected_count == 1

def test_transitive_caller_detected():
    G = nx.DiGraph()
    G.add_edge("A", "B")  # A -> B
    G.add_edge("B", "C")  # B -> C

    res = compute_blast_radius(G, ["C"])
    assert res.directly_affected == ["B"]
    assert res.transitively_affected == ["A"]
    assert res.all_affected == ["A", "B"]

def test_changed_symbol_excluded_from_affected():
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "A")

    res = compute_blast_radius(G, ["A", "B"])
    assert res.directly_affected == []
    assert res.transitively_affected == []
    assert res.all_affected == []

def test_symbol_not_in_graph_ignored():
    G = nx.DiGraph()
    G.add_node("A")

    res = compute_blast_radius(G, ["UNKNOWN_SYM"])
    assert res.changed_symbols == ["UNKNOWN_SYM"]
    assert res.directly_affected == []
    assert res.transitively_affected == []
    assert res.all_affected == []

def test_cycle_detected():
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "A")

    res = compute_blast_radius(G, ["B"])
    assert res.cycles_detected is True
    assert res.directly_affected == ["A"]

def test_deterministic_ordering():
    G = nx.DiGraph()
    G.add_edge("Z", "C")
    G.add_edge("X", "C")
    G.add_edge("M", "X")

    res1 = compute_blast_radius(G, ["C"])
    res2 = compute_blast_radius(G, ["C"])

    assert res1.directly_affected == ["X", "Z"]
    assert res1.transitively_affected == ["M"]
    assert res1.all_affected == ["M", "X", "Z"]
    assert res1 == res2

def test_all_affected_is_union():
    G = nx.DiGraph()
    G.add_edge("A", "C")
    G.add_edge("B", "C")
    G.add_edge("D", "B")

    res = compute_blast_radius(G, ["C"])
    expected_union = sorted(set(res.directly_affected) | set(res.transitively_affected))
    assert res.all_affected == expected_union
