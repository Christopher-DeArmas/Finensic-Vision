"""Unit tests for the pure cycle-detection helper."""

from app.graph import TransferEdge, find_cycles


def _edge(a, b, tid):
    return TransferEdge(src_customer_id=a, dst_customer_id=b, transaction_id=tid, amount=1.0)


def test_detects_simple_ring():
    edges = [_edge(1, 2, 10), _edge(2, 3, 11), _edge(3, 1, 12)]
    cycles = find_cycles(edges)
    assert len(cycles) == 1
    assert set(cycles[0]) == {1, 2, 3}


def test_ignores_non_cyclic_chain():
    edges = [_edge(1, 2, 10), _edge(2, 3, 11), _edge(3, 4, 12)]
    assert find_cycles(edges) == []


def test_ignores_two_node_mutual_by_default():
    # A <-> B is only 2 nodes; min_nodes defaults to 3.
    edges = [_edge(1, 2, 10), _edge(2, 1, 11)]
    assert find_cycles(edges) == []
