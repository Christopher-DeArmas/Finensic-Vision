"""Pure transfer-graph utilities used by the circular-transfer rule.

No database access here: callers pass in a list of ``TransferEdge`` tuples and
receive back adjacency structures and detected cycles. This keeps cycle
detection unit-testable in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransferEdge:
    """A directed money movement between two customers."""

    src_customer_id: int
    dst_customer_id: int
    transaction_id: int
    amount: float


def build_adjacency(edges: list[TransferEdge]) -> dict[int, list[tuple[int, int]]]:
    """Return ``{src: [(dst, transaction_id), ...]}``."""
    adjacency: dict[int, list[tuple[int, int]]] = {}
    for e in edges:
        if e.src_customer_id == e.dst_customer_id:
            continue  # ignore self-loops
        adjacency.setdefault(e.src_customer_id, []).append(
            (e.dst_customer_id, e.transaction_id)
        )
    return adjacency


def _canonical(cycle: list[int]) -> tuple[int, ...]:
    """Rotate a cycle so its smallest node is first, for de-duplication."""
    if not cycle:
        return tuple()
    i = cycle.index(min(cycle))
    return tuple(cycle[i:] + cycle[:i])


def find_cycles(
    edges: list[TransferEdge],
    min_nodes: int = 3,
    max_nodes: int = 5,
) -> list[list[int]]:
    """Find simple directed cycles with ``min_nodes``..``max_nodes`` members.

    Detects patterns like A -> B -> C -> A. Bounded DFS is sufficient for the
    demo's sparse transfer graph.
    """
    adjacency = build_adjacency(edges)
    seen: set[tuple[int, ...]] = set()
    cycles: list[list[int]] = []

    def dfs(start: int, current: int, path: list[int], visited: set[int]) -> None:
        for nxt, _txn in adjacency.get(current, []):
            if nxt == start and len(path) >= min_nodes:
                canon = _canonical(path)
                if canon not in seen:
                    seen.add(canon)
                    cycles.append(list(canon))
            elif nxt not in visited and len(path) < max_nodes:
                visited.add(nxt)
                path.append(nxt)
                dfs(start, nxt, path, visited)
                path.pop()
                visited.discard(nxt)

    for node in list(adjacency.keys()):
        dfs(node, node, [node], {node})

    return cycles


def cycle_transaction_ids(
    cycle: list[int], edges: list[TransferEdge]
) -> list[int]:
    """Transaction ids realizing the edges of ``cycle`` (consecutive members)."""
    edge_lookup: dict[tuple[int, int], list[int]] = {}
    for e in edges:
        edge_lookup.setdefault(
            (e.src_customer_id, e.dst_customer_id), []
        ).append(e.transaction_id)

    txn_ids: list[int] = []
    n = len(cycle)
    for i in range(n):
        src = cycle[i]
        dst = cycle[(i + 1) % n]
        txn_ids.extend(edge_lookup.get((src, dst), []))
    return txn_ids
