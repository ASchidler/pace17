import networkx as nx


class CostVsTerminalDistanceReduction:
    """ Removes all edges that are longer than the maximum distance between two terminals """
    def __init__(self):
        self.val = None

    def reduce(self, steiner, cnt, last_run):
        # Edge case, only one terminal
        if len(steiner.terminals) == 1:
            return 0

        # Find max distance
        if self.val is None:
            g = nx.Graph()
            [g.add_edge(t1, t2, weight=steiner.get_lengths(t1, t2))
                for t1 in steiner.terminals for t2 in steiner.terminals if t2 > t1]

            self.val = max([d for (u, v, d) in nx.maximum_spanning_edges(g)])

        terminal_edges = 0
        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > self.val:
                steiner.remove_edge(u, v)
                terminal_edges = terminal_edges + 1

        return terminal_edges

    def post_process(self, solution):
        return solution, False
