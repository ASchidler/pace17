import sys
import networkx as nx


class MstHeuristic:
    def __init__(self, steiner):
        self.steiner = steiner
        self.mst = {}

    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def calculate(self, n, set_id, ts):
        # Only one terminal
        if len(ts) == 1:
            return self.steiner.get_lengths(n, ts[0])

        # Calculate MST costs
        cost = self.calc_mst(ts, set_id)

        # Find minimum pairwise distance
        min_val = sys.maxint
        for i in range(0, len(ts)):
            t1 = ts[i]
            l1 = self.steiner.get_lengths(t1, n)
            for j in range(i + 1, len(ts)):
                t2 = ts[j]
                min_val = min(min_val, l1 + self.steiner.get_lengths(t2, n))

        return (min_val + cost) / 2

    def calc_mst(self, ts, set_id):
        """Calculate the costs of an MST using networkx"""
        if set_id in self.mst:
            return self.mst[set_id]

        g = nx.Graph()

        for i in range(0, len(ts)):
            t1 = ts[i]
            for j in range(i + 1, len(ts)):
                t2 = ts[j]
                g.add_edge(t1, t2, weight=self.steiner.get_lengths(t1, t2))

        cost = 0

        for (u, v, d) in list(nx.minimum_spanning_edges(g)):
            cost = cost + d['weight']

        self.mst[set_id] = cost
        return cost
