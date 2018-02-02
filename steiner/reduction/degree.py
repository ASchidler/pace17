import networkx as nx
import sys


# Removed nodes with degree 1 (non-terminal) and merges nodes with degree 2
class DegreeReduction:

    def __init__(self):
        self._merged = {}

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))

        old = sys.maxint

        while old > len(nx.nodes(steiner.graph)):
            old = len(nx.nodes(steiner.graph))
            for n, degree in nx.degree(steiner.graph):
                if degree == 1 and n not in steiner.terminals:
                    steiner.graph.remove_node(n)
                    break
                elif degree == 2 and n not in steiner.terminals:
                    nb = list(nx.neighbors(steiner.graph, n))
                    w1 = steiner.graph[n][nb[0]]['weight']
                    w2 = steiner.graph[n][nb[1]]['weight']

                    wo = sys.maxint
                    if steiner.graph.has_edge(nb[0], nb[1]):
                        wo = steiner.graph[nb[0]][nb[1]]

                    if w1 + w2 < wo:
                        steiner.graph.add_edge(nb[0], nb[1], weight=w1+w2)
                        steiner.graph.remove_node(n)
                        self._merged[(nb[0], nb[1], w1 + w2)] = [(nb[0], n, w1), (nb[1], n, w2)]
                        break

        print "Degree run " + str(track - len(nx.nodes(steiner.graph)))

        return track - len(nx.nodes(steiner.graph))

