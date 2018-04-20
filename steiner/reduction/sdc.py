from ntdk import NtdkReduction


class SdcReduction:
    def __init__(self, search_limit=40):
        self._done = False
        self._search_limit = search_limit

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.graph.edges) / len(steiner.graph.nodes) > 5:
            return 0

        track = len(steiner.graph.edges)

        # TODO: Combine SDC and NTDK to reuse edge results
        count = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            if d >= NtdkReduction.modified_dijkstra(steiner, u, v, d + 1, self._search_limit, True):
                steiner.remove_edge(u, v)
                count += 1

        if count > 0:
            steiner.invalidate_dist(+1)

        return track - len(steiner.graph.edges)

    def post_process(self, solution):
        return solution, False
