import sys
import networkx as nx


class TerminalDistanceReduction:
    """ Removes all edges that are longer than the maximum distance between two terminals """

    def reduce(self, steiner):
        terminal_edges = 0
        max_val = 0
        for t1 in steiner.terminals:
            min_val = sys.maxint
            for t2 in steiner.terminals:
                if t1 != t2:
                    dist = steiner.get_lengths(t1, t2)
                    min_val = min(min_val, dist)

            if min_val != sys.maxint:
                max_val = max(max_val, min_val)

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > max_val:
                steiner.graph.remove_edge(u, v)
                terminal_edges = terminal_edges + 1

        return terminal_edges

    def post_process(self, solution):
        return solution
