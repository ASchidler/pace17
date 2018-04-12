import ntdk
import networkx as nx


class SdcReduction:
    def reduce(self, steiner, cnt, last_run):
        if len(nx.edges(steiner.graph)) > 1000 and len(nx.edges(steiner.graph)) / len(nx.nodes(steiner.graph)) > 4:
            return 0

        count = 0
        edge_count = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            edge_count += 1

            if d >= ntdk.NtdkReduction.modified_dijkstra(steiner, u, v, d + 1, True):
                steiner.remove_edge(u, v)
                count += 1

        return count

    def post_process(self, solution):
        return solution, False
