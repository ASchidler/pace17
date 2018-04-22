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

        # Calc steiner tree including n rooted at r
        r = self.solver.root_node
        ts = set(ts)
        ts.add(n)
        result = da.DualAscent.calc2(self.steiner.graph, r, ts)

        return result[0]

