from sys import maxint


class ReachabilityReduction:
    def __init__(self):
        self._removed = {}
        self._done = False

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.graph.nodes) == 1:
            return 0

        track = len(steiner.graph.nodes)

        approx_nodes = set(steiner.get_approximation().tree.nodes)

        for n in list(steiner.graph.nodes):
            if n not in approx_nodes:
                min_val1 = maxint
                min_val2 = maxint
                max_val = 0

                for t in steiner.terminals:
                    d = steiner.get_lengths(t, n)
                    if d < min_val2:
                        if d < min_val1:
                            min_val2 = min_val1
                            min_val1 = d
                        else:
                            min_val2 = d

                    max_val = max(max_val, d)

                # Remove if this is fulfilled
                if min_val1 + max_val >= steiner.get_approximation().cost:
                    steiner.graph.remove_node(n)
                # Otherwise introduce artificial edges
                elif min_val1 + min_val2 + max_val >= steiner.get_approximation().cost:
                    nb = list(steiner.graph.neighbors(n))
                    # Introduce artificial edges
                    # TODO: find good value. At some point (10 is known, 6 is also too high) this becomes extremely slow
                    if len(nb) <= 5:
                        for i in range(0, len(nb)):
                            n1 = nb[i]
                            c1 = steiner.graph[n][n1]['weight']
                            for j in range(i+1, len(nb)):
                                n2 = nb[j]
                                c2 = steiner.graph[n][n2]['weight']

                                if steiner.add_edge(n1, n2, c1 + c2):
                                    self._removed[(n1, n2, c1 + c2)] = [(n, n1, c1), (n, n2, c2)]

                        steiner.remove_node(n)

        return track - len(steiner.graph.nodes)

    def post_process(self, solution):
        change = False
        for (k, v) in self._removed.items():
            if solution[0].has_edge(k[0], k[1]) and solution[0][k[0]][k[1]]['weight'] == k[2]:
                solution[0].remove_edge(k[0], k[1])
                solution[0].add_edge(v[0][0], v[0][1], weight=v[0][2])
                solution[0].add_edge(v[1][0], v[1][1], weight=v[1][2])
                change = True

        return solution, change
