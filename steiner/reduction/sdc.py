from ntdk import NtdkReduction


class SdcReduction:
    def reduce(self, steiner, cnt, last_run):
        if len(steiner.graph.edges) > 1000 and len(steiner.graph.edges) / len(steiner.graph.nodes) > 4:
            return 0

        count = 0
        edge_count = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            edge_count += 1

            if d >= NtdkReduction.modified_dijkstra(steiner, u, v, d + 1, True):
                steiner.remove_edge(u, v)
                count += 1

        return count

    def post_process(self, solution):
        return solution, False
