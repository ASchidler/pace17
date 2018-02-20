import networkx as nx


class LongEdgeReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def reduce(self, steiner):
        track = len(nx.edges(steiner.graph))

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > steiner.get_steiner_lengths(u, v):
                steiner.graph.remove_edge(u, v)

        return track - len(nx.edges(steiner.graph))

    def post_process(self, solution):
        return solution, False
