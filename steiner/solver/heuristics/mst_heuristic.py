from networkx import Graph, minimum_spanning_edges


class MstHeuristic:
    def __init__(self, steiner):
        self.steiner = steiner
        self.mst = {}

    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def calculate(self, n, set_id, ts, cost):
        # This guides the solver to the approximated result first
        # if n in self.steiner.get_approximation().get_descendants() and \
        #         all(t in self.steiner.get_approximation().get_descendants(self.steiner)[n] for t in ts):
        #     return 0

        length = self.steiner.get_lengths

        # Only one terminal
        if len(ts) == 1:
            for t in ts:
                return length(t, n)

        # Calculate MST costs
        if set_id in self.mst:
            cost = self.mst[set_id]
        else:
            cost = self.calc_mst(ts)
            self.mst[set_id] = cost

        # Find minimum pairwise distance
        min_val = []

        for (t, l) in self.steiner.closest_terminals[n]:
            if t in ts:
                min_val.append(l)

            if len(min_val) == 2:
                break

        return (min_val[0] + min_val[1] + cost) / 2

    def calc_mst(self, ts):
        """Calculate the costs of an MST using networkx"""

        g = Graph()
        length = self.steiner.get_lengths
        edge = g.add_edge

        # Cartesian product
        [edge(t1, t2, weight=length(t1, t2)) for t1 in ts for t2 in ts if t2 > t1]
        cost = sum(d['weight'] for u, v, d in minimum_spanning_edges(g))
        return cost
