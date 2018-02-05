import sys
import networkx as nx


class VoronoiReduction:
    """Approximates the maximum edge length using distances between voronoi areas"""

    def __init__(self):
        self.voronoi_areas = None

    def find_areas(self, steiner):
        """ Adds each node to the right terminal's voronoi area"""

        self.voronoi_areas = {}
        for t in steiner.terminals:
            self.voronoi_areas[t] = set()

        for n in nx.nodes(steiner.graph):
            if n not in steiner.terminals:
                min_val = sys.maxint
                min_node = None

                for t in steiner.terminals:
                    c = steiner.get_lengths(n, t)
                    if c < min_val:
                        min_val = c
                        min_node = t

                self.voronoi_areas[min_node].add(n)

    def find_exit_sum(self, steiner):
        """ Find exit node, i.e. those nodes closest but not in the current area and calculate the total distance """

        if self.voronoi_areas is None:
            self.find_areas(steiner)

        exit_sum = 0
        exit_max1 = 0
        exit_max2 = 0

        for (t, r) in self.voronoi_areas.items():
            min_val = sys.maxint
            for n in nx.nodes(steiner.graph):
                if n not in r:
                    min_val = min(min_val, steiner.get_lengths(t, n))

            exit_sum = exit_sum + min_val
            if min_val >= exit_max1:
                exit_max2 = exit_max1
                exit_max1 = min_val

        return exit_sum - exit_max1 - exit_max2

    def reduce(self, steiner):
        if self.voronoi_areas is None:
            self.find_areas(steiner)

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
                cnt = cnt + 2

            # Search for closest terminal
            for (t, r) in self.voronoi_areas.items():
                if u in r:
                    total = total + steiner.get_lengths(u, t)
                    cnt = cnt + 1

                if v in r:
                    total = total + steiner.get_lengths(v, t)
                    cnt = cnt + 1

                # Found terminal for both nodes in edge
                if cnt == 2:
                    break

            # Is the edge too long?
            if d + total + exit_sum > steiner.get_approximation().cost:
                steiner.graph.remove_edge(u, v)

        return track - len(nx.edges(steiner.graph))

    def post_process(self, solution):
        return solution
