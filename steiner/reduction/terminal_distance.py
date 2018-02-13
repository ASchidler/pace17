import sys
import networkx as nx


class CostVsTerminalDistanceReduction:
    """ Removes all edges that are longer than the maximum distance between two terminals """

    def reduce(self, steiner):
        terminal_edges = 0
        max_val = 0
        ts = list(steiner.terminals)
        for i in range(0, len(ts)):
            t1 = ts[i]

            for j in range(i+1, len(ts)):
                t2 = ts[j]

                dist = steiner.get_lengths(t1, t2)
                max_val = max(max_val, dist)

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > max_val:
                steiner.graph.remove_edge(u, v)
                terminal_edges = terminal_edges + 1

        return terminal_edges

    def post_process(self, solution):
        return solution
