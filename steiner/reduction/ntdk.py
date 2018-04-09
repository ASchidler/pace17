import networkx as nx
import itertools
import sys
import heapq as hq
from collections import defaultdict


class NtdkReduction:
    """ Removes all edges that are longer than the distance to the closest terminal """

    def __init__(self):
        self._removed = {}

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))

        for n in list(nx.nodes(steiner.graph)):
            nb = list(nx.all_neighbors(steiner.graph, n))
            degree = len(nb)
            true_for_all = True

            if n not in steiner.terminals and 2 < degree <= 4:
                nb.sort()
                total_edge_sum = sum(steiner.graph[n][b]['weight'] for b in nb)

                # Calc distances, more memory efficient than calculating it all beforehand
                dist = {(x, y): self.modified_dijkstra(steiner, x, y, total_edge_sum) for x in nb for y in nb if y > x}

                # Powersets
                for power_set in xrange(1, 1 << degree):
                    # Create complete graph
                    power_graph = nx.Graph()
                    edge_sum = 0

                    for i in xrange(0, degree):
                        if ((1 << i) & power_set) > 0:
                            n1 = nb[i]
                            edge_sum = edge_sum + steiner.graph[n][n1]['weight']

                            for j in xrange(i + 1, degree):
                                if ((1 << j) & power_set) > 0:
                                    n2 = nb[j]
                                    w = dist[(n1, n2)]
                                    power_graph.add_edge(n1, n2, weight=w)

                    mst = nx.minimum_spanning_tree(power_graph)
                    mst_sum = mst.size(weight='weight')
                    true_for_all = true_for_all and mst_sum <= edge_sum

                if true_for_all:
                    nb = list(nx.neighbors(steiner.graph, n))
                    # Introduce artificial edges
                    for (n1, n2) in ((x, y) for x in nb for y in nb if y > x):
                        c1 = steiner.graph[n][n1]['weight']
                        c2 = steiner.graph[n][n2]['weight']
                        if c1 + c2 <= dist[(n1, n2)]:
                            if steiner.add_edge(n1, n2, c1 + c2):
                                self._removed[(n1, n2, c1 + c2)] = [(n, n1, c1), (n, n2, c2)]

                    steiner.remove_node(n)

        steiner._lengths = {}
        return track - len(nx.nodes(steiner.graph))

    def post_process(self, solution):
        change = False
        cost = solution[1]
        for (k, v) in self._removed.items():
            if solution[0].has_edge(k[0], k[1]) and solution[0][k[0]][k[1]]['weight'] == k[2]:
                solution[0].remove_edge(k[0], k[1])
                cost -= self.add_edge(v[0][0], v[0][1], v[0][2], solution[0])
                cost -= self.add_edge(v[1][0], v[1][1], v[1][2], solution[0])
                change = True

        return (solution[0], cost), change

    def add_edge(self, u, v, d, g):
        if not g.has_edge(u, v):
            g.add_edge(u, v, weight=d)
            return 0

        if g[u][v]['weight'] > d:
            diff = g[u][v]['weight'] - d
            g[u][v]['weight'] = d
            return diff

        return d

    @staticmethod
    def modified_dijkstra(steiner, u, v, cut_off, restrict=False):
        scanned1 = NtdkReduction.modified_dijkstra_sub(steiner, u, v, cut_off)
        scanned2 = NtdkReduction.modified_dijkstra_sub(steiner, v, u, cut_off)

        sd = scanned1[v] if v in scanned1 else sys.maxint
        if u in scanned2:
            sd = min(sd, scanned2[u])

        for (n, c) in scanned1.items():
            if n in scanned2:
                if n in steiner.terminals:
                    sd = min(sd, max(scanned1[n], scanned2[n]))
                else:
                    sd = min(sd, scanned1[n] + scanned2[n])

        if not restrict and steiner.graph.has_edge(u, v):
            sd = min(sd, steiner.graph[u][v]['weight'])

        return sd

    @staticmethod
    # TODO: You can actually stop at already scanned nodes from the first run
    def modified_dijkstra_sub(steiner, u, v, cut_off):
        queue = [[0, u]]
        visited = set()
        scanned = defaultdict(lambda: sys.maxint)

        while len(queue) > 0:
            c_val = hq.heappop(queue)
            n = c_val[1]

            if n in visited:
                continue
            if n == v or c_val[0] > cut_off:
                break
            # Do not skip the first node, even if it is a terminal
            elif n in steiner.terminals and n != u:
                continue
            # Do not search too far
            elif len(visited) > 400:
                break

            for n2 in nx.neighbors(steiner.graph, n):
                cost = c_val[0] + steiner.graph[n][n2]['weight']

                # Do not use current edge
                if (min(n, n2) != min(u, v) or max(n, n2) != max(u, v)) and cost < scanned[n2]:
                    scanned[n2] = cost
                    hq.heappush(queue, [cost, n2])

        return scanned