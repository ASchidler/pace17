from sys import maxint


class ShortLinkPreselection:
    """Checks if the edges bridging Voronoi regions may be contracted"""

    def __init__(self):
        self.deleted = []
        self.merged = []
        self._done = False

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.terminals) <= 2:
            return 0

        steiner.requires_dist(1)

        track = len(steiner.graph.edges)
        closest = steiner.get_closest

        # Find bridging edges
        bridging_edges = {t: (maxint, None) for t in steiner.terminals}
        second_val = {t: maxint for t in steiner.terminals}

        # TODO: When is this valid? Since finding one edge may invalidate this...
        for (u, v, d) in steiner.graph.edges(data='weight'):
            t1 = closest(u)[0][0]
            t2 = closest(v)[0][0]

            if t1 != t2:
                if d < bridging_edges[t1][0]:
                    second_val[t1] = bridging_edges[t1][0]
                    bridging_edges[t1] = (d, t2, u, v)
                elif d < second_val[t1]:
                    second_val[t1] = d

                if d < bridging_edges[t2][0]:
                    second_val[t2] = bridging_edges[t2][0]
                    bridging_edges[t2] = (d, t1, u, v)
                elif d < second_val[t2]:
                    second_val[t2] = d

        for t in list(steiner.terminals):
            # May have been removed in between
            if t not in steiner.terminals:
                continue

            d, t2, u, v = bridging_edges[t]
            # Edge vanished in previous contraction. If t2 isn't a terminal anymore, the voronoi areas changed
            if not steiner.graph.has_edge(u, v) or t2 not in steiner.terminals:
                continue

            # There always exists a boundary edge. If there is no second largest edge, we can contract
            total = closest(u)[0][1] + d + closest(v)[0][1]

            if second_val[t] >= total:
                # Store
                self.deleted.append((u, v, d))

                # Contract, prefer to contract into a terminal
                if v in steiner.terminals:
                    u, v = v, u

                for e in steiner.contract_edge(u, v):
                    self.merged.append(e)

        track -= len(steiner.graph.edges)
        if track > 0:
            steiner._voronoi_areas = None
            steiner._closest_terminals = None
            steiner.invalidate_steiner(1)
            steiner.invalidate_dist(1)
            steiner.invalidate_approx(1)

        return track

    def post_process(self, solution):
        change = False
        cost = solution[1]

        if not self._done:
            for (n1, n2, w) in self.deleted:
                solution[0].add_edge(n1, n2, weight=w)
                cost = cost + w
                change = True
            self._done = True

        for (e1, e2) in self.merged:
            if solution[0].has_edge(e1[0], e1[1]):
                if solution[0][e1[0]][e1[1]]['weight'] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return (solution[0], cost), change
