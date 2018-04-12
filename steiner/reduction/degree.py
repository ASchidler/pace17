import networkx as nx
import sys


class DegreeReduction:
    """ Removed nodes with degree 1 (non-terminal) and merges nodes with degree 2 """

    def __init__(self):
        self._removed = {}

    def reduce(self, steiner, cnt, last_run):
        track = len(nx.nodes(steiner.graph))

        old = sys.maxint

        while old > len(nx.nodes(steiner.graph)):
            old = len(nx.nodes(steiner.graph))
            for n, degree in nx.degree(steiner.graph):
                if degree == 1 and n not in steiner.terminals:
                    steiner.remove_node(n)
                    break
                elif degree == 2 and n not in steiner.terminals:
                    nb = list(nx.neighbors(steiner.graph, n))
                    w1 = steiner.graph[n][nb[0]]['weight']
                    w2 = steiner.graph[n][nb[1]]['weight']

                    if steiner.add_edge(nb[0], nb[1], w1+w2):
                        self._removed[(nb[0], nb[1], w1 + w2)] = [(nb[0], n, w1), (nb[1], n, w2)]
                    steiner.remove_node(n)
                    break

        return track - len(nx.nodes(steiner.graph))

    def post_process(self, solution):
        change = False
        for (k, v) in self._removed.items():
            if solution[0].has_edge(k[0], k[1]) and solution[0][k[0]][k[1]]['weight'] == k[2]:
                solution[0].remove_edge(k[0], k[1])
                solution[0].add_edge(v[0][0], v[0][1], weight=v[0][2])
                solution[0].add_edge(v[1][0], v[1][1], weight=v[1][2])
                change = True

        return solution, change
