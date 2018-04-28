import reduction.dual_ascent as da
from math import log, ceil
import networkx as nx
from sys import maxint

def solve(steiner):
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

    min_result = maxint

    # Initialize
    result = {}
    for n in steiner.graph.nodes:
        for i in xrange(0, len(terminals)):
            result[(1 << i) + (n << terminal_bits)] = dists[n][terminal_ids[i]]

    for set_size in range(2, len(terminals) + 1):
        # Overall subsets of the current length

        # Initialize first subset
        subset = reduce(lambda x, y: x | y, ((1 << i) for i in xrange(0, set_size)))
        while subset <= max_terminals:
            # Find mapping between enumeration and subsets
            mapping = {}
            cnt = 0
            for i in xrange(0, t_cnt):
                if (1 << i) & subset > 0:
                    mapping[cnt] = (1 << i)
                    cnt += 1

            # Find decompositions
            # set_size - 1 since the subsets are symmetric
            for i in range(1, 1 << (set_size - 1)):
                s1 = reduce(lambda x, y: x | y, (mapping[j] for j in xrange(0, set_size) if ((1 << j) & i) > 0))
                s2 = subset ^ s1

                for n in steiner.graph.nodes:
                    n_code = (n << terminal_bits)
                    code = n_code + subset
                    c1 = n_code + s1
                    c2 = n_code + s2
                    result[code] = min(result[c1] + result[c2], result.setdefault(code, max))

            # Propagate
            for n1 in steiner.graph.nodes:
                n1_code = (n1 << terminal_bits) + subset
                for n2 in steiner.graph.nodes:
                    if n1 != n2:
                        n2_code = (n2 << terminal_bits) + subset
                        result[n1_code] = min(result[n1_code], dists[n1][n2] + result[n2_code])

                if set_size == t_cnt:
                    min_result = min(min_result, result[n1_code])

            t = (subset | (subset - 1)) + 1
            subset = t | ((((t & -t) / (subset & -subset)) >> 1) - 1)

    return min_result
