import sys
import networkx as nx


class ReachabilityReduction:
    def __init__(self):
        self._removed = {}

    def reduce(self, steiner):
        track = len(nx.nodes(steiner.graph))

        approx_nodes = nx.nodes(steiner.get_approximation().tree)

        for n in list(nx.nodes(steiner.graph)):
            if n not in approx_nodes:
                min_val1 = sys.maxint
                min_val2 = sys.maxint
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
                # TODO: Is this correct?
                if min_val2 == sys.maxint:
                    min_val2 = min_val1

                if min_val1 != sys.maxint:
                    # Remove if this is fulfilled
                    if min_val1 + max_val >= steiner.get_approximation().cost:
                        steiner.graph.remove_node(n)
                    # Otherwise introduce artificial edges
                    elif min_val1 + min_val2 + max_val >= steiner.get_approximation().cost:
                        nb = list(nx.neighbors(steiner.graph, n))
                        # Introduce artificial edges
                        # TODO: find good value. At some point (10 is known) this becomes extremely slow
                        if len(nb) <= 4:
                            for i in range(0, len(nb)):
                                n1 = nb[i]
                                c1 = steiner.graph[n][n1]['weight']
                                for j in range(i+1, len(nb)):
                                    n2 = nb[j]
                                    c2 = steiner.graph[n][n2]['weight']

                                    if steiner.add_edge(n1, n2, c1 + c2):
                                        self._removed[(n1, n2, c1 + c2)] = [(n, n1, c1), (n, n2, c2)]

                        steiner.graph.remove_node(n)

        total = track - len(nx.nodes(steiner.graph))
        print "Reachability " + str(total)

        return total
