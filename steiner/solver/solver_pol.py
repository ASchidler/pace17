import reduction.dual_ascent as da
from math import log, ceil
import networkx as nx
from sys import maxint

def partitioned_solve(steiner):
    max_vertex = max(steiner.graph.nodes)
    vertex_bits = int(ceil(log(max_vertex, 2)))
    terminal_bits = len(steiner.terminals)
    terminal_decoder = (1 << terminal_bits) - 1
    vertex_decoder = ((1 << vertex_bits) - 1) << terminal_bits
    terminals = list(steiner.terminals)
    t_cnt = len(terminals)
    max_terminals = (1 << len(terminals)) - 1
    terminal_ids = {i: terminals[i] for i in xrange(0, len(terminals))}
    dists = dict(nx.all_pairs_dijkstra_path_length(steiner.graph))

    ub = steiner.get_approximation().cost
    results = [[[set() for _ in xrange(0, t_cnt + 1)] for _ in xrange(0, ub + 1)] for _ in xrange(0, max_vertex + 1)]
    min_result = maxint

    nodes = list(steiner.graph.nodes)
    nodes.sort()

    # Initialize
    for n in steiner.graph.nodes:
        for i in xrange(0, len(terminals)):
            d = dists[n][terminals[i]]
            if d <= ub:
                results[n][d][1].add(1 << i)

    for c_cost in xrange(1, ub + 1):
        for c_size in xrange(2, t_cnt + 1):
            for n in steiner.graph.nodes:
                # Merge
                for c1 in xrange(0, c_cost / 2 + 1):
                    c2 = c_cost - c1

                    for s1 in xrange(0, c_size / 2 + 1):
                        s2 = c_size - s1

                        for c_set1 in results[n][c1][s1]:
                            for c_set2 in results[n][c2][s2]:
                                if c_set1 & c_set2 == 0:
                                    results[n][c_cost][c_size].add(c_set1 | c_set2)

            # Propagate
            for i1 in xrange(0, len(nodes)):
                n1 = nodes[i1]
                for i2 in xrange(i1 + 1, len(nodes)):
                    n2 = nodes[i2]
                    d = c_cost - dists[n1][n2]
                    if d >= 0:
                        results[n1][c_cost][c_size].update(x for x in results[n2][d][c_size])
                        results[n2][c_cost][c_size].update(x for x in results[n1][d][c_size])

        # Check
        for n in steiner.graph.nodes:
            if len(results[n][c_cost][len(terminals)]) > 0:
                return c_cost


def solve(steiner):
    max_vertex = max(steiner.graph.nodes)
    terminals = list(steiner.terminals)
    t_cnt = len(terminals)
    dists = dict(nx.all_pairs_dijkstra_path_length(steiner.graph))

    ub = steiner.get_approximation().cost
    results = [[{} for _ in xrange(0, t_cnt + 1)] for _ in xrange(0, max_vertex + 1)]

    nodes = list(steiner.graph.nodes)
    nodes.sort()

    # Initialize
    for n in steiner.graph.nodes:
        for i in xrange(0, len(terminals)):
            d = dists[n][terminals[i]]
            if d <= ub:
                results[n][1][1 << i] = d

    for set_size in range(2, len(terminals) + 1):
        # Overall subsets of the current length

        for s1 in xrange(1, set_size / 2 + 1):
            s2 = set_size - s1

            for n in nodes:
                for (v1, c1) in results[n][s1].items():
                    for (v2, c2) in results[n][s2].items():
                        total = c1 + c2
                        if (v1 & v2) == 0 and total <= ub:
                            new_set = v1 | v2
                            if results[n][set_size].setdefault(new_set, total) > total:
                                results[n][set_size][new_set] = total

        for i1 in xrange(0, len(nodes)):
            n1 = nodes[i1]
            for i2 in xrange(i1 + 1, len(nodes)):
                n2 = nodes[i2]
                d = dists[n1][n2]

                for (s, v) in results[n1][set_size].items():
                    total = v + d
                    if total <= ub and results[n2][set_size].setdefault(s, total) > total:
                            results[n2][set_size][s] = total

                for (s, v) in results[n2][set_size].items():
                    total = v + d
                    if total <= ub and results[n1][set_size].setdefault(s, total):
                            results[n1][set_size][s] = total

    min_val = min(c for n in nodes for (_, c) in results[n][t_cnt].items())

    return min_val
