import sys
import networkx as nx


class CutReachabilityReduction:

    def __init__(self):
        self._terminal_minimums = None
        self._terminal_sum = 0

    # Find smallest neighbours
    def find_minimums(self, steiner):
        self._terminal_minimums = {}

        for t in steiner.terminals:
            min_val = sys.maxint

            for n in nx.neighbors(steiner.graph, t):
                w = steiner.graph[t][n]['weight']
                min_val = min(w, min_val)

                self._terminal_minimums[t] = min_val
                self._terminal_sum = self._terminal_sum + min_val

    def reduce(self, steiner, cnt, last_run):
        if len(steiner.graph.nodes) == 1:
            return 0

        cut_cnt = 0

        # Always recalculate so that it adapts to changing terminal set
        self.find_minimums(steiner)

        approx_nodes = nx.nodes(steiner.get_approximation().tree)
        for n in list(nx.nodes(steiner.graph)):
            if n not in approx_nodes:
                min_val1 = sys.maxint
                min_val2 = sys.maxint
                min_dist1 = sys.maxint
                min_dist2 = sys.maxint
                n1 = None
                n2 = None

                for (t, s) in self._terminal_minimums.items():
                    d = steiner.get_lengths(t, n)
                    diff = d - s

                    if diff < min_val2:
                        if diff < min_val1:
                            min_val2 = min_val1
                            min_dist2 = min_dist1
                            n2 = n1
                            min_val1 = diff
                            n1 = t
                            min_dist1 = d
                        else:
                            min_dist2 = d
                            min_val2 = diff
                            n2 = t

                # TODO: Is this correct
                if min_val2 == sys.maxint:
                    min_val2 = min_val1
                    n2 = n1
                    min_dist2 = min_dist1

                min_sum = min_dist1 + min_dist2

                for t in steiner.terminals:
                    if t != n1 and t != n2:
                        min_sum = min_sum + self._terminal_minimums[t]

                if min_sum >= steiner.get_approximation().cost:
                    steiner.remove_node(n)
                    cut_cnt = cut_cnt + 1

        return cut_cnt

    def post_process(self, solution):
        return solution, False


