from networkx import Graph, minimum_spanning_edges


class CostVsTerminalDistanceReduction:
    """ Removes all edges that are longer than the maximum distance between two terminals """
    def __init__(self):
        self.enabled = True
        self._done = False

    def reduce(self, steiner, cnt, last_run):
        # Edge case, only one terminal
        if len(steiner.terminals) == 1 or not (self.enabled or last_run):
            return 0

        steiner._lengths = {}

        # Find max distance
        g = Graph()
        [g.add_edge(t1, t2, weight=steiner.get_lengths(t1, t2))
            for t1 in steiner.terminals for t2 in steiner.terminals if t2 > t1]
        val = max([d for (u, v, d) in minimum_spanning_edges(g)])

        terminal_edges = 0
        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > val:
                steiner.remove_edge(u, v)
                terminal_edges = terminal_edges + 1

        self.enabled = terminal_edges > 0

        return terminal_edges

    def post_process(self, solution):
        return solution, False
