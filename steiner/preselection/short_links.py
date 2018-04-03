import sys
import networkx as nx


class ShortLinkPreselection:

    def __init__(self):
        self.deleted = []
        self.merged = []
        self._done = False

    def reduce(self, steiner):
        track = 0
        vor = steiner.get_voronoi()

        for (t, r) in vor.items():
            # May have been removed in between
            if t not in steiner.terminals:
                continue

            # Find shortest and second shortest edge out
            min1 = (0, 0, sys.maxint)
            min2 = (0, 0, sys.maxint)

            for (u, v, d) in steiner.graph.edges(data='weight'):
                u_in = (u == t or u in r)
                v_in = (v == t or v in r)

                # Bridges region?
                if u_in ^ v_in:
                    if d < min1[2]:
                        min2 = min1
                        min1 = (u, v, d)
                    elif d < min2[2]:
                        min2 = (u, v, d)

            # TODO: If there is no min2, contract?
            if min1[2] < sys.maxint and min2[2] < sys.maxint:
                other_t, dist = steiner.get_closest(min1[1])[0]
                total = steiner.get_lengths(t, min1[0]) + min1[2] + dist

                if min2[2] >= total:
                    track = track + 1

                    # Store
                    self.deleted.append((min1[0], min1[1], min1[2]))

                    # Contract, prefer to contract into a terminal
                    n1, n2 = (min1[0], min1[1]) if min1[0] in steiner.terminals else (min1[1], min1[0])

                    for e in steiner.contract_edge(n1, n2):
                        self.merged.append(e)

                    # Fix voronoi if terminals are not merged
                    if t != n1 and t != n2 and other_t != n1 and other_t != n2:
                        for n in list(vor[t]):
                            if steiner.get_lengths(t, n) > steiner.get_lengths(other_t, n):
                                vor[t].remove(n)
                                vor[other_t].add(n)

                        for n in list(vor[other_t]):
                            if steiner.get_lengths(other_t, n) > steiner.get_lengths(t, n):
                                vor[other_t].remove(n)
                                vor[t].add(n)

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

