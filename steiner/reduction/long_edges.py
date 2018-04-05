import networkx as nx
import preselection as pr
import sys

class LongEdgeReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def __init__(self):
        self.runs = 0

    def reduce(self, steiner):
        track = len(nx.edges(steiner.graph))

        if self.runs > 0:
            steiner.refresh_steiner_lengths()

        sorted_edges = sorted(steiner.graph.edges(data='weight'), key=lambda x: x[2])

        # TODO: Calculate once and update...
        mst = nx.minimum_spanning_tree(steiner.graph)

        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            if d > steiner.get_steiner_lengths(u, v, d):
                steiner.remove_edge(u, v)
            elif d >= self._min_crossing(mst, u, v, d, sorted_edges, steiner):
                steiner.remove_edge(u, v)
                steiner.refresh_steiner_lengths()

        self.runs = self.runs + 1
        return track - len(nx.edges(steiner.graph))

    def post_process(self, solution):
        return solution, False

    def _min_crossing(self, mst, n1, n2, cutoff, sorted_edges, steiner):
        """Finds the r value of an edge. I.e. the smallest edge bridging the mst cut by (n1, n2) in G
        Since we need a value > than d, we use a cutoff value to shorten calculation"""

        target_edge = (n1, n2, steiner.graph[n1][n2]['weight'])
        steiner.graph.remove_edge(n1, n2)

        c_max = 0

        try:
            path = list(nx.dijkstra_path(steiner.graph, n1, n2))
            for i in range(1, len(path)):
                c_max = max(c_max, steiner.graph[path[i]][path[i-1]]['weight'])

        except nx.NetworkXNoPath:
            c_max = sys.maxint

        steiner.graph.add_edge(target_edge[0], target_edge[1], weight=target_edge[2])
        return c_max

        if not mst.has_edge(n1, n2):
            return cutoff

        queue = [n1]
        nodes = set()

        # Calculate the cut
        while len(queue) > 0:
            n = queue.pop()
            nodes.add(n)

            for b in nx.neighbors(mst, n):
                if b != n2 and b not in nodes:
                    queue.append(b)

        # Find minimum edge bridging the cut
        for (u, v, d) in sorted_edges:
            if d > cutoff:
                return sys.maxint

            if (u in nodes and v not in nodes) or (v in nodes and u not in nodes):
                return d

        return sys.maxint
