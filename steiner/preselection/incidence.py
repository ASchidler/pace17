import networkx as nx
import sys


class IncidenceReduction:
    """ Checks the incidence of terminals, of degree one or the closest is a terminal, preselects edge """

    def reduce(self, steiner):
        # Incidence check
        incidence = 0
        for t in steiner.terminals:
            min_val = sys.maxint
            min_node = None
            neighbors = 0

            for n in nx.neighbors(steiner.graph, t):
                neighbors = neighbors + 1
                w = steiner.graph[t][n]['weight']
                if w < min_val:
                    min_node = n
                    min_val = w

            if min_node in steiner.terminals or neighbors == 1:
                incidence = incidence + 1

        return incidence

    def post_process(self, solution):
        return solution, False