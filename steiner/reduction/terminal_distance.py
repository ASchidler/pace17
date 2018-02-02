import sys
import networkx as nx


# Removes all edges that are longer than the maximum distance between two terminals
class TerminalDistanceReduction:

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

        print "terminal edge " + str(terminal_edges)
