import sys
import networkx as nx


class MstHeuristic:
    def __init__(self, steiner):
        self.steiner = steiner
        self.mst = {}

    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def calculate(self, n, set_id, ts):
        length = self.steiner.get_lengths

        # Only one terminal
        if len(ts) == 1:
            return length(ts[0], n)

        # Calculate MST costs
        if set_id in self.mst:
            cost = self.mst[set_id]
        else:
            cost = self.calc_mst(ts)
            self.mst[set_id] = cost

        # Find minimum pairwise distance
        min_val = min_val2 = sys.maxint

        for t in ts:
            lg = length(t, n)
            if lg < min_val:
                min_val2, min_val = min_val, lg
            elif lg < min_val2:
                min_val2 = lg

        return (min_val + min_val2 + cost) / 2

    def calc_mst(self, ts):
        """Calculate the costs of an MST using networkx"""

        g = nx.Graph()
        length = self.steiner.get_lengths
        edge = g.add_edge

        # Cartesian product
        [edge(t1, t2, weight=length(t1, t2)) for t1 in ts for t2 in ts if t2 > t1]
        cost = sum(d['weight'] for u, v, d in nx.minimum_spanning_edges(g))
        return cost
