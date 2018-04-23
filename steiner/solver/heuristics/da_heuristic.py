import reduction.dual_ascent as da
from networkx import dijkstra_path_length, single_source_dijkstra_path_length


class DaHeuristic:
    def __init__(self, steiner):
        self.steiner = steiner
        self.solver = None
        self.calculated = {}
        self._qry_cnt = 0
        self._hit_at = {}

    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def calculate(self, n, set_id, ts):
        # Simplest "tree", just an edge
        if len(ts) == 1:
            for t in ts:
                return self.steiner.get_lengths(t, n)

        self._qry_cnt += 1
        try:
            d = self.calculated[set_id][n]
            self._hit_at[set_id] = self._qry_cnt

            return d
        except KeyError:
            self.precalc(ts, set_id)
            self._hit_at[set_id] = self._qry_cnt
            d = self.calculated[set_id][n]

        if self._qry_cnt % 5000 == 0:
            for (s, c) in self._hit_at.items():
                if self._qry_cnt - c > 5000:
                    self._hit_at.pop(s)
                    self.calculated.pop(s)

        return d

    # TODO: Remove, this is just for testing
    def calculate2(self, n, set_id, ts):
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

    def precalc(self, ts, set_id):
        r = self.solver.root_node
        ts = set(ts)
        result = da.DualAscent.calc2(self.steiner.graph, r, ts)

        root_dist = single_source_dijkstra_path_length(result[1], r)
        # for (n2, dta) in result[1]._pred[r].items():
        #     result[1].remove_edge(n2, r)

        vor = da.DualAscent.voronoi(result[1], [t for t in ts if t != r])

        nodes = {}
        bnd = result[0]

        for (t, v) in vor.items():
            for (n, d) in v.items():
                nodes[n] = root_dist[n] + bnd + d

        self.calculated[set_id] = nodes
