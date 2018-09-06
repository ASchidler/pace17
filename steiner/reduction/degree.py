from sys import maxint


class DegreeReduction:
    """ Removed nodes with degree 1 (non-terminal) and merges nodes with degree 2
    Also tries to contract edges for terminals (degree 1 or of closest vertex is a terminal)
    """

    def __init__(self):
        self._removed = {}
        self._contracted = []
        self._selected = []
        self._done = False
        # Mechanism to not contract in the first run
        self._ran = False

    def reduce(self, steiner, prev_cnt, curr_cnt):
        track = len(steiner.graph.edges)
        t_cnt = 0

        old = maxint

        while old > len(steiner.graph.nodes):
            old = len(steiner.graph.nodes)
            for n in list(steiner.graph.nodes):
                if not steiner.graph.has_node(n):
                    continue

                dg = steiner.graph.degree(n)
                if dg == 1:
                    # Nodes of degree1 => remove
                    if n not in steiner.terminals:
                        steiner.remove_node(n)
                    # Terminals of degree 1 => Simply contract
                    elif self._ran:
                        nb = next(steiner.graph.neighbors(n))
                        self._contracted.append((n, nb, steiner.graph[n][nb]['weight']))
                        steiner.move_terminal(n, nb)
                        steiner.remove_node(n)
                        t_cnt += 1

                # Nodes of degree 2 => merge
                elif dg == 2 and n not in steiner.terminals:
                    nb = list(steiner.graph.neighbors(n))
                    w1 = steiner.graph[n][nb[0]]['weight']
                    w2 = steiner.graph[n][nb[1]]['weight']

                    if steiner.add_edge(nb[0], nb[1], w1+w2):
                        self._removed[(nb[0], nb[1], w1 + w2)] = [(nb[0], n, w1), (nb[1], n, w2)]
                    steiner.remove_node(n)

                # Terminals of higher degree? Merge if the nearest node is a terminal
                elif self._ran and dg >= 2 and n in steiner.terminals:
                    min_val, min_nb = maxint, None
                    for n2 in steiner.graph.neighbors(n):
                        w = steiner.graph[n][n2]['weight']

                        if w < min_val or (w == min_val and n2 in steiner.terminals):
                            min_val, min_nb = w, n2

                    if min_nb in steiner.terminals:
                        self._contracted.append((n, min_nb, min_val))

                        for e in steiner.contract_edge(n, min_nb):
                            self._selected.append(e)
                        t_cnt += 1

        if t_cnt > 0:
            steiner.invalidate_steiner(1)
            steiner.invalidate_dist(1)
            steiner.invalidate_approx(1)

        self._ran = True
        return track - len(steiner.graph.edges)

    def post_process(self, solution):
        change = False
        cost = solution[1]

        if not self._done:
            for (n1, n2, w) in self._contracted:
                solution[0].add_edge(n1, n2, weight=w)
                cost += w
                change = True
            self._done = True

        for (k, v) in self._removed.items():
            if solution[0].has_edge(k[0], k[1]) and solution[0][k[0]][k[1]]['weight'] == k[2]:
                solution[0].remove_edge(k[0], k[1])
                solution[0].add_edge(v[0][0], v[0][1], weight=v[0][2])
                solution[0].add_edge(v[1][0], v[1][1], weight=v[1][2])
                change = True

        for (e1, e2) in self._selected:
            if solution[0].has_edge(e1[0], e1[1]):
                if solution[0][e1[0]][e1[1]]['weight'] == e1[2]:
                    solution[0].remove_edge(e1[0], e1[1])
                    solution[0].add_edge(e2[0], e2[1], weight=e2[2])
                    change = True

        return (solution[0], cost), change
