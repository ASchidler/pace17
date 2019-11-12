from sys import maxint


class MstHeuristic:
    """Heuristic that uses the MST of the terminals in the distance graph (halved) as a lower bound"""
    def __init__(self, steiner):
        self.steiner = steiner
        self.mst = {}
        self.solver = None
        self.desc = None

    def calculate(self, n, set_id):
        length = self.steiner.get_lengths

        # Only one terminal
        if set_id == 0:
            return length(self.solver.root_node, n)

        # Calculate MST costs
        ts = self.solver.to_list(set_id)
        ts.append(self.solver.root_node)

        try:
            cost = self.mst[set_id]
        except KeyError:
            cost = self.calc_mst(ts)
            self.mst[set_id] = cost

        # Find minimum pairwise distance
        min_val = []

        for (t, l) in self.steiner.get_closest(n):
            if t in ts:
                min_val.append(l)

            if len(min_val) == 2:
                break

        return (min_val[0] + min_val[1] + cost) / 2

    def calc_mst(self, ts):
        """Calculate the costs of a MST using Prim's algorithm"""

        # use prim since we have a full graph
        length = self.steiner.get_lengths
        min_edge = [maxint for _ in ts]
        taken = [False for _ in ts]

        idx = -1
        sum_edges = 0

        # Init
        min_edge[0] = 0

        for _ in range(0, len(ts)):
            # Find minimum edge
            val = maxint
            for k in range(0, len(ts)):
                if min_edge[k] < val:
                    val = min_edge[k]
                    idx = k

            # Add vertex to MST
            taken[idx] = True
            min_edge[idx] = maxint
            sum_edges += val

            # Adjust minimum edges
            for k in range(0, len(ts)):
                if not taken[k]:
                    min_edge[k] = min(min_edge[k], length(ts[idx], ts[k]))

        return sum_edges
