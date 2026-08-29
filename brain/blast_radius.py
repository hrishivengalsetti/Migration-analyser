import networkx as nx
from models import BlastRadius

def compute_blast_radius(graph: nx.DiGraph, changed_symbols: list[str]) -> BlastRadius:
    changed_set = set(changed_symbols)
    all_ancestors = set()
    directly_affected = set()

    for sym in changed_symbols:
        if sym not in graph:
            continue

        try:
            ancestors = nx.ancestors(graph, sym)
            all_ancestors.update(ancestors)
        except nx.NetworkXError:
            pass

        for predecessor in graph.predecessors(sym):
            if predecessor not in changed_set:
                directly_affected.add(predecessor)

    # Exclude changed symbols themselves from affected sets
    all_ancestors -= changed_set
    directly_affected -= changed_set

    transitively_affected = all_ancestors - directly_affected

    # Check cycles in relevant upstream subgraph
    relevant_nodes = set(changed_symbols).intersection(graph.nodes()).union(all_ancestors)
    if relevant_nodes:
        subgraph = graph.subgraph(relevant_nodes)
        cycles_detected = not nx.is_directed_acyclic_graph(subgraph)
    else:
        cycles_detected = False

    all_affected_sorted = sorted(directly_affected | transitively_affected)

    return BlastRadius(
        changed_symbols=sorted(changed_symbols),
        directly_affected=sorted(directly_affected),
        transitively_affected=sorted(transitively_affected),
        all_affected=all_affected_sorted,
        cycles_detected=cycles_detected,
        total_affected_count=len(all_affected_sorted),
    )
