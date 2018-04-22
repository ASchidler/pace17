import reduction.dual_ascent as da
from networkx import dijkstra_path_length, single_source_dijkstra_path_length


class DaHeuristic:
    def __init__(self, steiner):
        self.steiner = steiner
        self.solver = None

    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def calculate(self, n, set_id, ts):
        # Simplest "tree", just an edge
        if len(ts) == 1:
            for t in ts:
                return self.steiner.get_lengths(t, n)
        # MST -> Exact
        if len(ts) == 2:
            ts = list(ts)
            l1 = self.steiner.get_lengths(ts[0], n)
            l2 = self.steiner.get_lengths(ts[1], n)
            l3 = self.steiner.get_lengths(ts[1], ts[0])
            return min(l1 + l2, min(l1 + l3, l2 + l3))

        # Calc steiner tree including n rooted at r
        r = self.solver.root_node
        ts = set(ts)
        ts.add(n)
        result = da.DualAscent.calc2(self.steiner.graph, r, ts)

        return result[0]

