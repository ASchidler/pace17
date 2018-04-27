import heapq as hq
from collections import defaultdict
from sys import maxint
from networkx import minimum_spanning_edges, Graph


class NtdkReduction:
    """ Removes all edges that are longer than the distance to the closest terminal """

    def __init__(self, restricted, search_limit=40, only_last=False, max_degree=4):
        self._removed = {}
        self._restricted = restricted
        self._done = False
        self._search_limit = search_limit
        self._only_last = only_last
        self._max_degree = max_degree

    def reduce(self, steiner, cnt, last_run):
        # if len(steiner.graph.edges) / len(steiner.graph.nodes) >= 3:
        #     return 0

        change = False
        if self._only_last and not last_run:
            return 0

        if self._restricted:
            steiner.requires_steiner_dist(1)

        track = len(steiner.graph.edges)
        nbs = steiner.graph._adj

        for n in list(steiner.graph.nodes):
            if n not in steiner.terminals and 2 < steiner.graph.degree(n) <= self._max_degree:
                nb = nbs[n].items()
                total_edge_sum = sum(dta['weight'] for (x, dta) in nb)

                # Calc distances, more memory efficient than calculating it all beforehand
                if not self._restricted:
                    dist = {(x, y): self.modified_dijkstra(steiner, x, y, total_edge_sum, self._search_limit, False) for (x, tt1) in nb for (y, tt2) in nb if y > x}
                else:
                    dist = {(x, y): steiner.get_steiner_lengths(x, y, 0) for (x, tt1) in nb for (y, tt2) in nb if y > x}

                # Choose the easier calculation for the case of degree 3
                if len(nb) == 3:
                    dist_itm = dist.values()
                    nb_sum = min([dist_itm[0] + dist_itm[1], dist_itm[0] + dist_itm[2], dist_itm[1] + dist_itm[2]])
                    true_for_all = nb_sum <= total_edge_sum
                else:
                    true_for_all = True
                    # Sort for access to dist dict
                    nb.sort(key=lambda x: x[0])

                    # The case for 4 is slightly optimized
                    if len(nb) == 4:
                        # Powersets
                        # Set num will be the index of the neighbor not to include, plus -1 for the full set
                        # Only works for degree 4!
                        for set_num in xrange(-1, len(nb)):
                            power_graph = Graph()
                            edge_sum = 0

                            for i in xrange(0, len(nb)):
                                if i != set_num:
                                    n1, dta = nb[i]
                                    edge_sum += dta['weight']

                                    for j in xrange(i + 1, len(nb)):
                                        if j != set_num:
                                            n2 = nb[j][0]
                                            w = dist[(n1, n2)]
                                            power_graph.add_edge(n1, n2, weight=w)

                            mst_sum = sum(d['weight'] for (u, v, d) in minimum_spanning_edges(power_graph))
                            true_for_all = true_for_all and mst_sum <= edge_sum
                    else:
                        for power_set in xrange(1, 1 << len(nb)):
                            power_graph = Graph()
                            edge_sum = 0
                            if bin(power_set).count("1") >= 3:
                                for i in xrange(0, len(nb)):
                                    if ((1 << i) & power_set) > 0:
                                        n1, dta = nb[i]
                                        edge_sum = edge_sum + dta['weight']

                                        for j in xrange(i + 1, len(nb)):
                                            if ((1 << j) & power_set) > 0:
                                                n2 = nb[j][0]
                                                w = dist[(n1, n2)]
                                                power_graph.add_edge(n1, n2, weight=w)

                                mst_sum = sum(d['weight'] for (u, v, d) in minimum_spanning_edges(power_graph))
                                true_for_all = true_for_all and mst_sum <= edge_sum

                        if not true_for_all:
                            break

                if true_for_all:
                    # Introduce artificial edges
                    for (n1, n2) in ((x, y) for (x, tt1) in nb for (y, tt2) in nb if y > x):
                        c1 = steiner.graph[n][n1]['weight']
                        c2 = steiner.graph[n][n2]['weight']
                        if c1 + c2 <= dist[(n1, n2)]:
                            if steiner.add_edge(n1, n2, c1 + c2):
                                self._removed[(n1, n2, c1 + c2)] = [(n, n1, c1), (n, n2, c2)]
                    steiner.remove_node(n)
                    change = True

        result = track - len(steiner.graph.edges)
        if change:
            steiner.invalidate_approx(-2)

        return result

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
    def modified_dijkstra(steiner, u, v, cut_off, depth_limit, restrict=False):
        scanned1 = NtdkReduction.modified_dijkstra_sub(steiner, u, v, cut_off, depth_limit)
        scanned2 = NtdkReduction.modified_dijkstra_sub(steiner, v, u, cut_off, depth_limit)

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
    def modified_dijkstra_sub(steiner, u, v, cut_off, depth_limit):
        queue = [[0, u]]
        scanned = defaultdict(lambda: maxint)

        scanned_edges = 0
        nb = steiner.graph._adj

        # Expand first node explicitly here, so no check in the loop is required to exclude edge
        for n2, dta in nb[u].items():
            if n2 != v:
                c = dta['weight']
                hq.heappush(queue, [c, n2])
                scanned[n2] = c

        # TODO: The limit constant has a big effect on the effectiveness of the reduction! SCIP uses values of up to 400
        while len(queue) > 0 and scanned_edges < depth_limit:
            c_val = hq.heappop(queue)
            n = c_val[1]

            if c_val[0] > cut_off:
                break
            # Do not use source or target and also stop at terminals
            elif n in steiner.terminals or n == v or n == u:
                continue

            for n2, dta in nb[n].items():
                scanned_edges += 1
                if scanned_edges > depth_limit:
                    break

                cost = c_val[0] + dta['weight']

                if (n2 not in scanned or cost < scanned[n2]) and cost <= cut_off:
                    scanned[n2] = cost
                    hq.heappush(queue, [cost, n2])

        return scanned
