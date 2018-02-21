import voronoi
import networkx as nx
import sys


class VoronoiNodeReduction(voronoi.VoronoiReduction):
    def find_mst(self, steiner):
        vor = steiner.get_voronoi()
        g = nx.Graph()

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

        max_edge = 0
        for (u, v, d) in g.edges(data='weight'):
            max_edge = max(max_edge, d)

        mst_cost = 0
        for (u, v, d) in nx.minimum_spanning_tree(g).edges(data='weight'):
            mst_cost = mst_cost + d

        return mst_cost - max_edge

    def reduce(self, steiner):
        if len(steiner.terminals) == 1:
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

        return track
