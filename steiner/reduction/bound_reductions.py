import networkx as nx
import sys


class BoundNodeReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def __init__(self):
        self.runs = 0

    def reduce(self, steiner):
        if len(steiner.terminals) < 2:
            return 0

        t_weight = 0
        radius = steiner.get_radius()
        cnt = 0

        for i in range(0, len(steiner.terminals) - 2):
            t_weight += radius[i][0]

        for n in list(nx.nodes(steiner.graph)):
            if n not in steiner.terminals:
                dists = steiner.get_closest(n)
                total = dists[0][1] + dists[1][1] + t_weight
                if total > steiner.get_approximation().cost or \
                        (total == steiner.get_approximation().cost and not steiner.get_approximation().tree.has_node(
                            n)):
                    steiner.remove_node(n)
                    cnt += 1

        return cnt

    def post_process(self, solution):
        return solution, False


class BoundEdgeReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def __init__(self):
        self.runs = 0

    def reduce(self, steiner):
        if len(steiner.terminals) < 2:
            return 0

        t_weight = 0
        radius = steiner.get_radius()
        cnt = 0

        for i in range(0, len(steiner.terminals) - 2):
            t_weight += radius[i][0]

        for (u, v, d) in steiner.graph.edges(data='weight'):
            dist1 = steiner.get_closest(u)[0]
            dist2 = steiner.get_closest(v)[0]

            if dist1[0] != dist2[0]:
                total = d + dist1[1] + dist2[1] + t_weight
            else:
                d12 = steiner.get_closest(u)[1][1]
                d22 = steiner.get_closest(v)[1][1]
                total = d + min(dist1[1] + d22, dist2[1] + d12) + t_weight

            if total > steiner.get_approximation().cost:
                steiner.remove_edge(u, v)
                cnt += 1

        return cnt

    def post_process(self, solution):
        return solution, False


class BoundNtdkReduction:
    """ Removes all edges that are longer than the distance to the closest terminal """

    def __init__(self):
        self._removed = {}

    def reduce(self, steiner):
        if len(steiner.terminals) < 3:
            return 0

        cnt = 0
        t_weight = 0
        radius = steiner.get_radius()

        for i in range(0, len(steiner.terminals) - 3):
            t_weight += radius[i][0]

        for n in list(nx.nodes(steiner.graph)):
            # TODO: Find a good upper bound
            if n not in steiner.terminals and 2 < steiner.graph.degree[n] <= 5:
                closest = steiner.get_closest(n)
                total = closest[0][1] + closest[1][1] + closest[2][1] + t_weight

                if total > steiner.get_approximation().cost or (total == steiner.get_approximation().cost and
                                                                not steiner.get_approximation().tree.has_node(n)):
                    nb = nx.neighbors(steiner.graph, n)
                    for (n1, n2) in ((x, y) for x in nb for y in nb if y > x):
                        c1 = steiner.graph[n][n1]['weight']
                        c2 = steiner.graph[n][n2]['weight']

                        if steiner.add_edge(n1, n2, c1 + c2):
                            self._removed[(n1, n2, c1 + c2)] = [(n, n1, c1), (n, n2, c2)]

                    steiner.remove_node(n)

        return cnt

    def post_process(self, solution):
        change = False
        for (k, v) in self._removed.items():
            if solution[0].has_edge(k[0], k[1]) and solution[0][k[0]][k[1]]['weight'] == k[2]:
                solution[0].remove_edge(k[0], k[1])
                solution[0].add_edge(v[0][0], v[0][1], weight=v[0][2])
                solution[0].add_edge(v[1][0], v[1][1], weight=v[1][2])
                change = True

        return solution, change


class BoundGraphReduction:
    """Removes all edges that are longer than the distance to the closest terminal. Also known as PTm test."""

    def __init__(self):
        self.runs = 0

    def reduce(self, steiner):
        if len(steiner.terminals) < 2:
            return 0

        cnt = 0
        g_prime = nx.Graph()
        vor = steiner.get_voronoi()
        lg = steiner.get_lengths

        for (t1, t2) in ((t1, t2) for t1 in steiner.terminals for t2 in steiner.terminals if t2 > t1):
            t1_vor = list(vor[t1])
            t2_vor = list(vor[t2])
            t1_vor.append(t1)
            t2_vor.append(t2)
            min_cost = sys.maxint

            for n1 in t1_vor:
                for n2 in t2_vor:
                    if steiner.graph.has_edge(n1, n2):
                        min_cost = min(min_cost, steiner.graph[n1][n2]['weight'] + min(lg(t1, n1), lg(t2, n2)))

            if min_cost < sys.maxint:
                g_prime.add_edge(t1, t2, weight=min_cost)

        mst_sum = 0
        mst_max = 0
        for (u, v, d) in nx.minimum_spanning_edges(g_prime):
            mst_sum += d['weight']
            mst_max = max(mst_max, d['weight'])

        mst_sum -= mst_max

        for n in list(nx.nodes(steiner.graph)):
            if n not in steiner.terminals:
                dists = steiner.get_closest(n)
                total = dists[0][1] + dists[1][1] + mst_sum
                if total > steiner.get_approximation().cost:
                    steiner.remove_node(n)
                    cnt += 1

        for (u, v, d) in steiner.graph.edges(data='weight'):
            total = steiner.get_closest(u)[0][1] + steiner.get_closest(v)[0][1] + mst_sum
            if total > steiner.get_approximation().cost:
                steiner.remove_edge(u, v)
                cnt += 1

        return cnt

    def post_process(self, solution):
        return solution, False
