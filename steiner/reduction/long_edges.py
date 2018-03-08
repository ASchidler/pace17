import networkx as nx


class LongEdgeReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def __init__(self):
        self.runs = 0

    def reduce(self, steiner):
        # Do not use if the graph is too big -> Memory constraints
        if len(steiner.graph.nodes) > 400:
            return 0

        track = len(nx.edges(steiner.graph))

        if self.runs > 0:
            steiner.refresh_steiner_lengths()

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > steiner.get_steiner_lengths(u, v):
                steiner.remove_edge(u, v)

        self.runs = self.runs + 1
        return track - len(nx.edges(steiner.graph))

    def post_process(self, solution):
        return solution, False
