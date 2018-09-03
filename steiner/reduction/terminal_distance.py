from networkx import Graph, minimum_spanning_edges
from sys import maxint


class CostVsTerminalDistanceReduction:
    """ Removes all edges that are longer than the maximum distance between two terminals """

    def __init__(self, threshold=0.01):
        self.enabled = True
        self._done = False
        self._threshold = threshold
        self._counter = maxint / 2

    def reduce(self, steiner, cnt, last_run):
        # Edge case, only one terminal
        if len(steiner.terminals) == 1 or not (self.enabled or last_run):
            return 0

        self._counter += cnt
        if self._counter < self._threshold * len(steiner.graph.edges):
            return 0
        else:
            self._counter = 0

        steiner.requires_dist(1)
        track = len(steiner.graph.edges)

        # Find max distance
        g = Graph()
        [g.add_edge(t1, t2, weight=steiner.get_lengths(t1, t2))
            for t1 in steiner.terminals for t2 in steiner.terminals if t2 > t1]
        val = max([d for (u, v, d) in minimum_spanning_edges(g)])

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > val:
                steiner.remove_edge(u, v)

        result = track - len(steiner.graph.edges)
        self.enabled = track > 0

        return result

    def post_process(self, solution):
        return solution, False
