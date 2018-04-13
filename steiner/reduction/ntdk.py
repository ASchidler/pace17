import heapq as hq
from collections import defaultdict
from sys import maxint
from networkx import minimum_spanning_edges, Graph


class NtdkReduction:
    """ Removes all edges that are longer than the distance to the closest terminal """

    def __init__(self, restricted):
        self._removed = {}
        self._restricted = restricted

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.graph.edges) / len(steiner.graph.nodes) >= 3:
            return 0

        if self._restricted:
            steiner.refresh_steiner_lengths()

        track = len(steiner.graph.nodes)

        for n in list(steiner.graph.nodes):
            if n not in steiner.terminals and 2 < steiner.graph.degree(n) <= 4:
                nb = list(steiner.graph.neighbors(n))
                true_for_all = True

                nb.sort()
                total_edge_sum = sum(steiner.graph[n][b]['weight'] for b in nb)

                # Calc distances, more memory efficient than calculating it all beforehand
                if not self._restricted:
                    dist = {(x, y): self.modified_dijkstra(steiner, x, y, total_edge_sum, self._restricted) for x in nb for y in nb if y > x}
                else:
                    dist = {(x, y): steiner.get_steiner_lengths(x, y, 0) for x in nb for y in nb if y > x}

                # Powersets
                # TODO: This could be done faster, i.e. don't create powersets of cardinality < 3
                for power_set in xrange(1, 1 << len(nb)):
                    # Create complete graph
                    power_graph = Graph()
                    edge_sum = 0

                    # Sets of size at least 3
                    if bin(power_set).count("1") >= 3:
                        for i in xrange(0, len(nb)):
                            if ((1 << i) & power_set) > 0:
                                n1 = nb[i]
                                edge_sum = edge_sum + steiner.graph[n][n1]['weight']

                                for j in xrange(i + 1, len(nb)):
                                    if ((1 << j) & power_set) > 0:
                                        n2 = nb[j]
                                        w = dist[(n1, n2)]
                                        power_graph.add_edge(n1, n2, weight=w)

                        mst_sum = sum(d['weight'] for (u, v, d) in minimum_spanning_edges(power_graph))
                        true_for_all = true_for_all and mst_sum <= edge_sum

                if true_for_all:
                    # Introduce artificial edges
                    for (n1, n2) in ((x, y) for x in nb for y in nb if y > x):
                        c1 = steiner.graph[n][n1]['weight']
                        c2 = steiner.graph[n][n2]['weight']
                        if c1 + c2 <= dist[(n1, n2)]:
                            if steiner.add_edge(n1, n2, c1 + c2):
                                self._removed[(n1, n2, c1 + c2)] = [(n, n1, c1), (n, n2, c2)]
                    steiner.remove_node(n)

        steiner._lengths = {}
        return track - len(steiner.graph.nodes)

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

        # If we found the other node use this dist. Scanned != Visited, therefore values may differ!
        sd = scanned1[v] if v in scanned1 else maxint
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
    def modified_dijkstra_sub(steiner, u, v, cut_off):
        queue = [[0, u]]
        visited = {u}
        scanned = defaultdict(lambda: maxint)
        scanned_edges = 0

        # Expand first node explicitly here, so no check in the loop is required to exclude edge
        for n2 in steiner.graph.neighbors(u):
            if n2 != v:
                c = steiner.graph[u][n2]['weight']
                hq.heappush(queue, [c, n2])
                scanned[n2] = c

        while len(queue) > 0 and scanned_edges < 40:
            c_val = hq.heappop(queue)
            n = c_val[1]

            if n in visited:
                continue
            if c_val[0] > cut_off:
                break
            # Do not skip the first node, even if it is a terminal
            elif n in steiner.terminals or n == v:
                continue

            for n2 in steiner.graph.neighbors(n):
                scanned_edges += 1
                if n2 not in visited:
                    cost = c_val[0] + steiner.graph[n][n2]['weight']

                    if cost < scanned[n2] and cost <= cut_off:
                        scanned[n2] = cost
                        hq.heappush(queue, [cost, n2])

        return scanned
