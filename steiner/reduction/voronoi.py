import sys
import networkx as nx


class VoronoiReduction:
    """Approximates the maximum edge length using distances between voronoi areas"""

    def __init__(self):
        self.enabled = True

    def find_exit_sum(self, steiner):
        """ Find exit node, i.e. those nodes closest but not in the current area and calculate the total distance """
        exit_sum = 0
        exit_max1 = 0
        exit_max2 = 0

        for (t, r) in steiner.get_voronoi().items():

            min_val = sys.maxint
            for n in nx.nodes(steiner.graph):
                if n not in r:
                    min_val = min(min_val, steiner.get_lengths(t, n))

            exit_sum = exit_sum + min_val

            if min_val > exit_max2:
                if min_val > exit_max1:
                    exit_max2 = exit_max1
                    exit_max1 = min_val
                else:
                    exit_max2 = min_val

        return exit_sum - exit_max1 - exit_max2

    def reduce(self, steiner, cnt, last_run):
        if not self.enabled and not last_run:
            return 0

        track = len(nx.edges(steiner.graph))
        exit_sum = self.find_exit_sum(steiner)

        # Check edges
        for (u, v, d) in list(steiner.graph.edges(data='weight')):
            # Find the distance to the closest terminals for each end of the edge
            total = 0
            cnt = 0
            # Terminals have distance 0 to itself
            if u in steiner.terminals:
                cnt = cnt + 1
            if v in steiner.terminals:
                cnt = cnt + 1

            # Search for closest terminal
            for (t, r) in steiner.get_voronoi().items():
                if u in r:
                    total = total + steiner.get_lengths(t, u)
                    cnt = cnt + 1

                if v in r:
                    total = total + steiner.get_lengths(t, u)
                    cnt = cnt + 1

                # Found terminal for both nodes in edge
                if cnt == 2:
                    break

            # Is the edge too long?
            if d + total + exit_sum > steiner.get_approximation().cost:
                steiner.remove_edge(u, v)

        result = track - len(nx.edges(steiner.graph))
        self.enabled = result > 0

        return result

    def post_process(self, solution):
        return solution, False
