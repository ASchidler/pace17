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

    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def calculate(self, n, set_id, ts, total):
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

        app = self.upper_bound[set_id]
        if n in app.tree.nodes:
            ub = app.cost
        else:
            for (n2, nd) in self._closest[n]:
                if app.tree.has_node(n2):
                    ub = app.cost + nd #multi_source_dijkstra_path_length(self.steiner.graph, app.tree.nodes)[1]
                    break

        gb = self.steiner.get_approximation().cost
        gb = min(ub, gb - total)
        print "Lower {} Upper {} Total {}".format(d, ub, ub - d)
        if d == ub:
            print "Match"
        elif d > ub:
            print "Exceeded"
        print "Lower {}".format(d)

        # Clean up to save memory
        if self._qry_cnt % 5000 == 0:
            for (s, c) in self._hit_at.items():
                if self._qry_cnt - c > 5000:
                    self._hit_at.pop(s)
                    self.calculated.pop(s)

        return max(0, d - max(0, (16 - (ub - d)) / 3))
        #return d

    def precalc(self, ts, set_id):
        r = self.solver.root_node
        ts = set(ts)
        result = da.DualAscent.calc3(self.steiner.graph, r, ts)

        nodes = {}
        bnd = result[0]
        # Do not add the distance to the closest terminal. As n is the linking node between the partial results
        # it may be a leaf for the heuristic!
        for (n, d) in single_source_dijkstra_path_length(result[1], r).items():
            nodes[n] = d + bnd

        self.calculated[set_id] = nodes
        self.find_new(set_id, result, ts, r)

    def find_new(self, set_id, result, ts, r):
        """Combines solution graphs into a new solution"""

        if self._closest is None:
            max_node = max(self.steiner.graph.nodes)
            self._closest = [None] * (max_node + 1)
            for n in self.steiner.graph.nodes:
                self._closest[n] = [(n2, d) for (n2, d) in self.steiner.get_lengths(n).items()]
                self._closest[n].sort(key=lambda x: x[1])

        # self.upper_bound[set_id] = {n: 0 for n in self.steiner.graph.node}
        # return
        dg = sg.SteinerGraph()
        dg.graph = self.steiner.graph
        dg.terminals = ts

        #(bnd, g, r) = result

        # 0 length paths
        # pths = single_source_dijkstra_path(g, r, cutoff=1)
        # for t in (t for t in ts if t != r):
        #     for i in range(1, len(pths[t])):
        #         u, v = pths[t][i-1], pths[t][i]
        #         u, v = min(u, v), max(u, v)
        #         dg.add_edge(u, v, self.steiner.graph[u][v]['weight'])
        # for (u, v, d) in g.edges(data='weight'):
        #     if d == 0:
        #         dg.add_edge(u, v, self.steiner.graph[u][v]['weight'])

        app = sa.SteinerApproximation(dg, True,  limit=1)
        self.upper_bound[set_id] = app
