import ntdk


class SdcReduction:
    def reduce(self, steiner):
        count = 0
        edge_count = 0
        for (u, v, d) in steiner.graph.edges(data='weight'):
            edge_count += 1
            # Iteration limit
            if edge_count > 2000:
                break

            if d >= ntdk.NtdkReduction.modified_dijkstra(steiner, u, v, d + 1, True):
                steiner.remove_edge(u, v)
                count += 1

        return count

    def post_process(self, solution):
        return solution, False
