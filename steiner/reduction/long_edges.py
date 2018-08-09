import ntdk
from sys import maxint
from collections import defaultdict
import heapq as hq

class LongEdgeReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def __init__(self, delete_equal, threshold=0.01, equal_search_limit=40):
        self.runs = 0
        self._delete_equal = delete_equal
        self._done = False
        self._equal_search_limit = equal_search_limit
        self._threshold = threshold
        self._counter = maxint / 2

    def reduce(self, steiner, cnt, last_run):
        steiner.requires_steiner_dist(1)

        track = len(steiner.graph.edges)

        equal_edges = []

        self._counter += cnt
        # if self._counter < self._threshold * len(steiner.graph.edges):
        #     return 0
        # else:
        #     self._counter = 0

        delete = []
        for (u, v, d) in steiner.graph.edges(data='weight'):
            sl = steiner.get_steiner_lengths(u, v, d)
            if d > sl:
                delete.append((u, v))
            elif d == sl:
                equal_edges.append((u, v, d))

        for u, v in delete:
            steiner.remove_edge(u, v)

        for t in steiner.terminals:
            for n in list(steiner.graph.neighbors(t)):
                if steiner.graph[n][t]['weight'] > steiner.get_lengths(t, n):
                    steiner.remove_edge(n, t)

        if self._delete_equal and (cnt == 0 or last_run) and len(steiner.graph.edges) / len(steiner.graph.nodes) < 10:
            for (u, v, d) in equal_edges:
                if steiner.graph.has_edge(u, v) and \
                        d >= ntdk.NtdkReduction.modified_dijkstra(steiner, u, v, d + 1, self._equal_search_limit, True):
                    steiner.remove_edge(u, v)

        result = track - len(steiner.graph.edges)
        if result > 0:
            steiner.invalidate_dist(-1)

        self.runs = self.runs + 1
        return result

    def post_process(self, solution):
        return solution, False
