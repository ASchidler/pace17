import math
import sys


class TspHeuristic:
    """This is a heuristic that calculates the tour (TSP) of the terminals in the distance graph as lower bound"""

    # Tests found it really slow for more complex instances
    def __init__(self, steiner):
        self.tsp = {}
        self.steiner = steiner

    def calculate(self, n, set_id, ts):
        if len(ts) == 1:
            return self.steiner.get_lengths(ts[0], n)

        # So we know that smaller terminals always are first
        ts.sort()

        cost = self.get_tsp_for_set(set_id, ts)

        # Find the smallest tour, by adding the node to all possible hamiltonian paths
        min_val = sys.maxint
        for i in range(0, len(ts)):
            t1 = ts[i]
            d1 = self.steiner.get_lengths(t1, n)
            for j in range(i + 1, len(ts)):
                t2 = ts[j]
                d2 = self.steiner.get_lengths(t2, n)
                min_val = min(min_val, d1 + d2 + cost[(t1, t2)])

        return int(math.ceil(min_val / 2.0))

    def get_tsp_for_set(self, set_id, ts):
        """ Calculates the Hamiltonian paths for all possible endpoint pairs in the set"""

        # Check if known
        if set_id in self.tsp:
            return self.tsp[set_id]

        # List of remaining nodes
        nodes = list(ts)
        # Reference list, copy to not change the result
        ts = list(nodes)
        # Init result
        self.tsp[set_id] = {}

        for i in range(0, len(ts)):
            # Use ts, otherwise the index would change for nodes
            t1 = ts[i]
            nodes.remove(t1)

            for j in range(i + 1, len(ts)):
                t2 = ts[j]
                # Do not add the endpoint. This would make it a tour, but we need hamiltonian paths
                self.tsp[set_id][(t1, t2)] = self.calc_tsp(t1, nodes, t2)  # + self.steiner.get_lengths(t1, t2)

            nodes.append(t1)
        return self.tsp[set_id]

    def calc_tsp(self, s, nodes, l):
        """ Calculates the shortest path from s to l visiting all nodes """
        if len(nodes) == 1:
            return self.steiner.get_lengths(s, l)

        min_val = sys.maxint
        # Remove current element for recursive calls
        nodes.remove(l)

        # Reduce the problem to the one with one fewer terminal ob take the minimum over all possible nodes
        for i in range(0, len(nodes)):
            new_l = nodes[i]
            sub_tsp = self.calc_tsp(s, nodes, new_l)
            min_val = min(min_val, sub_tsp + self.steiner.get_lengths(new_l, l))

        # Leaves the parameter list in its previous state
        nodes.append(l)
        nodes.sort()

        return min_val
