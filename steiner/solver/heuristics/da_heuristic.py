import reduction.dual_ascent as da
from networkx import dijkstra_path_length, single_source_dijkstra_path_length, single_source_dijkstra_path, multi_source_dijkstra_path_length
import steiner_graph as sg
import steiner_approximation as sa

# TODO: Try both heuristics at the start, choose better one for the remainder
class DaHeuristic:
    def __init__(self, steiner):
        self.steiner = steiner
        self.solver = None
        self.calculated = {}
        self.upper_bound = {}
        self._qry_cnt = 0
        self._hit_at = {}
        self._closest = None
        self._method = None

    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def calculate(self, n, set_id, ts):
        # Simplest "tree", just an edge
        if len(ts) == 1:
            for t in ts:
                return self.steiner.get_lengths(t, n)

        self._qry_cnt += 1

        # Load precalculated value or calculate if not existing
        try:
            d = self.calculated[set_id][n]
            self._hit_at[set_id] = self._qry_cnt

            return d
        except KeyError:
            self.precalc(ts, set_id)
            self._hit_at[set_id] = self._qry_cnt
            d = self.calculated[set_id][n]

        # Clean up to save memory
        if self._qry_cnt % 15000 == 0:
            for (s, c) in self._hit_at.items():
                if self._qry_cnt - c > 15000:
                    self._hit_at.pop(s)
                    self.calculated.pop(s)

        return d

    def precalc(self, ts, set_id):
        r = self.solver.root_node

        if self._method is None:
            result1 = da.DualAscent.calc3(self.steiner.graph, r, self.steiner.terminals)
            result2 = da.DualAscent.calc2(self.steiner.graph, r, self.steiner.terminals)
            self._method = da.DualAscent.calc2 if result2[0] >= result1[0] else da.DualAscent.calc3

        ts = set(ts)
        result = self._method(self.steiner.graph, r, ts)

        nodes = {}
        bnd = result[0]
        # Do not add the distance to the closest terminal. As n is the linking node between the partial results
        # it may be a leaf for the heuristic!
        for (n, d) in single_source_dijkstra_path_length(result[1], r).items():
            nodes[n] = d + bnd

        self.calculated[set_id] = nodes
