import ntdk

class LongEdgeReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def __init__(self, delete_equal):
        self.runs = 0
        self._delete_equal = delete_equal

    def reduce(self, steiner, cnt, last_run):
        track = len(steiner.graph.edges)

        # if self.runs > 0:
        steiner.refresh_steiner_lengths()

        equal_edges = []

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            sl = steiner.get_steiner_lengths(u, v, d)
            if d > sl:
                steiner.remove_edge(u, v)
            elif d == sl:
                equal_edges.append((u, v, d))

        for t in steiner.terminals:
            for n in list(steiner.graph.neighbors(t)):
                if steiner.graph[n][t]['weight'] > steiner.get_lengths(n, t):
                    steiner.remove_edge(n, t)

        if self._delete_equal and cnt == 0 and len(steiner.graph.edges) / len(steiner.graph.nodes) < 10:
            for (u, v, d) in equal_edges:
                if steiner.graph.has_edge(u, v) and \
                        d >= ntdk.NtdkReduction.modified_dijkstra(steiner, u, v, d + 1, True):
                    steiner.remove_edge(u, v)

        self.runs = self.runs + 1
        return track - len(steiner.graph.edges)

    def post_process(self, solution):
        return solution, False
