import voronoi
import networkx as nx
import sys


class VoronoiNodeReduction(voronoi.VoronoiReduction):
    def __init__(self):
        self.enabled = True

    def find_mst(self, steiner):
        vor = steiner.get_voronoi()
        g = nx.Graph()

        # Get the minimum connecting edges between regions
        for (u, v, d) in steiner.graph.edges(data='weight'):
            t1 = None
            t2 = None

            for (t, r) in vor.items():
                if t == u or u in r:
                    t1 = t
                if t == v or v in r:
                    t2 = t

                if t1 is not None and t2 is not None:
                    break

            if t1 != t2:
                cost = d + min(steiner.get_lengths(t1, u), steiner.get_lengths(t2, v))
                if g.has_edge(t1, t2):
                    if g[t1][t2]['weight'] > cost:
                        g[t1][t2]['weight'] = cost
                else:
                    g.add_edge(t1, t2, weight=cost)

        max_edge = max(d for u, v, d in g.edges(data='weight'))
        mst_cost = sum(d['weight'] for u, v, d in nx.minimum_spanning_edges(g))

        return mst_cost - max_edge

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.terminals) == 1 or not (self.enabled or last_run):
            return 0

        track = 0
        comp = min(self.find_exit_sum(steiner), self.find_mst(steiner))

        for n in list(nx.nodes(steiner.graph)):
            if n in steiner.terminals:
                continue

            min1 = sys.maxint
            min2 = sys.maxint

            for t in steiner.terminals:
                d = steiner.get_lengths(t, n)
                if d < min2:
                    if d < min1:
                        min2 = min1
                        min1 = d
                    else:
                        min2 = d

            if comp + min1 + min2 > steiner.get_approximation().cost:
                track = track + 1
                steiner.remove_node(n)

        self.enabled = track > 0

        return track
